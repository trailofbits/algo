"""Async subprocess wrapper for Ansible playbook execution."""

import asyncio
import json
import os
import re
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from .sessions import DeploymentStatus, Session, sessions

# Get the algo project root directory
ALGO_DIR = Path(__file__).parent.parent


def build_extra_vars(session: Session) -> dict[str, Any]:
    """Build the extra-vars dict for Ansible from session config."""
    config = session.config
    credentials = session.credentials

    # Map provider IDs to Ansible provider aliases
    provider_map = {
        "digitalocean": "digitalocean",
        "hetzner": "hetzner",
        "linode": "linode",
        "vultr": "vultr",
    }

    extra_vars: dict[str, Any] = {
        "provider": provider_map.get(session.provider, session.provider),
    }

    # Add credentials based on provider
    if session.provider == "digitalocean":
        extra_vars["do_token"] = credentials.get("do_token", "")
    elif session.provider == "hetzner":
        extra_vars["hcloud_token"] = credentials.get("hcloud_token", "")
    elif session.provider == "linode":
        extra_vars["linode_token"] = credentials.get("linode_token", "")
    elif session.provider == "vultr":
        # Vultr uses a different approach - write temp config file
        extra_vars["vultr_config"] = credentials.get("vultr_api_key", "")

    # Add server configuration
    if config.get("server_name"):
        extra_vars["server_name"] = config["server_name"]
    if config.get("region"):
        extra_vars["region"] = config["region"]

    # Add users list
    if config.get("users"):
        extra_vars["users"] = config["users"]

    # Add boolean options
    bool_options = [
        ("wireguard_enabled", "wireguard_enabled"),
        ("ipsec_enabled", "ipsec_enabled"),
        ("dns_adblocking", "dns_adblocking"),
        ("ssh_tunneling", "ssh_tunneling"),
        ("ondemand_cellular", "ondemand_cellular"),
        ("ondemand_wifi", "ondemand_wifi"),
        ("store_pki", "store_pki"),
    ]

    for config_key, ansible_var in bool_options:
        if config_key in config:
            extra_vars[ansible_var] = config[config_key]

    return extra_vars


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


async def run_playbook(session: Session) -> AsyncGenerator[str, None]:
    """Run ansible-playbook with streaming output.

    This function uses asyncio.create_subprocess_exec which is safe from
    shell injection - arguments are passed as a list, not interpolated.

    Args:
        session: The deployment session

    Yields:
        Lines of output from the playbook run
    """
    extra_vars = build_extra_vars(session)

    # Build command as list (safe - no shell interpolation)
    cmd = [
        "uv",
        "run",
        "ansible-playbook",
        "main.yml",
        "--extra-vars",
        json.dumps(extra_vars),
    ]

    # Set up environment
    env = os.environ.copy()
    env["ANSIBLE_FORCE_COLOR"] = "0"  # Disable colors for cleaner output
    env["ANSIBLE_NOCOLOR"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    try:
        # Start the process using create_subprocess_exec (safe, no shell)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(ALGO_DIR),
            env=env,
        )

        session.process = process
        session.status = DeploymentStatus.RUNNING
        await sessions.update(session)

        # Clear credentials from memory now that we've started
        session.clear_credentials()

        # Stream output line by line
        config_path_pattern = re.compile(r"configs/[\d.]+|configs/localhost")

        if process.stdout:
            async for line_bytes in process.stdout:
                line = strip_ansi(line_bytes.decode("utf-8", errors="replace")).rstrip()
                if line:
                    session.add_output(line)
                    yield line

                    # Try to capture config path from output
                    if match := config_path_pattern.search(line):
                        session.config_path = str(ALGO_DIR / match.group(0))

        # Wait for process to complete
        await process.wait()

        session.exit_code = process.returncode
        if process.returncode == 0:
            session.status = DeploymentStatus.SUCCESS
            yield "[SUCCESS] Deployment completed successfully!"
        else:
            session.status = DeploymentStatus.FAILED
            session.error = f"Playbook exited with code {process.returncode}"
            yield f"[ERROR] Deployment failed with exit code {process.returncode}"

    except asyncio.CancelledError:
        session.status = DeploymentStatus.CANCELLED
        session.error = "Deployment was cancelled"
        if session.process:
            session.process.terminate()
            await session.process.wait()
        yield "[CANCELLED] Deployment was cancelled"
        raise

    except Exception as e:
        session.status = DeploymentStatus.FAILED
        session.error = str(e)
        yield f"[ERROR] {e!s}"

    finally:
        session.process = None
        await sessions.update(session)


async def cancel_deployment(session: Session) -> bool:
    """Cancel a running deployment.

    Args:
        session: The session to cancel

    Returns:
        True if cancellation was successful
    """
    if session.process and session.status == DeploymentStatus.RUNNING:
        session.process.terminate()
        try:
            await asyncio.wait_for(session.process.wait(), timeout=10.0)
        except TimeoutError:
            session.process.kill()
            await session.process.wait()

        session.status = DeploymentStatus.CANCELLED
        session.error = "Deployment was cancelled by user"
        await sessions.update(session)
        return True

    return False
