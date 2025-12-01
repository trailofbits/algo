"""Algo VPN Web UI - Starlette application."""

import asyncio
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from .providers import PROVIDERS, validate_credentials
from .runner import cancel_deployment, run_playbook
from .sessions import sessions

# Paths
APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
ALGO_DIR = APP_DIR.parent

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# === Page Routes ===


async def index(request: Request) -> Response:
    """Main page with provider selection and configuration form."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "providers": PROVIDERS,
        },
    )


async def deploy_page(request: Request) -> Response:
    """Deployment progress page."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session:
        return HTMLResponse(
            "<h1>Session not found</h1><p>This deployment session has expired or does not exist.</p>",
            status_code=404,
        )

    provider = PROVIDERS.get(session.provider)
    return templates.TemplateResponse(
        request,
        "deploy.html",
        {
            "session": session,
            "provider": provider,
        },
    )


async def success_page(request: Request) -> Response:
    """Success page with config downloads."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session:
        return HTMLResponse(
            "<h1>Session not found</h1><p>This deployment session has expired or does not exist.</p>",
            status_code=404,
        )

    # List config files
    config_files: list[dict[str, Any]] = []
    if session.config_path and Path(session.config_path).exists():
        config_dir = Path(session.config_path)
        for file_path in sorted(config_dir.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(config_dir)
                config_files.append(
                    {
                        "name": str(rel_path),
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "is_qr": file_path.suffix == ".png",
                    }
                )

    provider = PROVIDERS.get(session.provider)
    return templates.TemplateResponse(
        request,
        "success.html",
        {
            "session": session,
            "provider": provider,
            "config_files": config_files,
        },
    )


# === API Routes ===


async def provider_form(request: Request) -> Response:
    """Return the credential form partial for a provider."""
    provider_id = request.path_params["provider"]
    provider = PROVIDERS.get(provider_id)

    if not provider:
        return HTMLResponse("<p>Unknown provider</p>", status_code=404)

    return templates.TemplateResponse(
        request,
        "partials/provider_form.html",
        {"provider": provider},
    )


async def validate_provider(request: Request) -> Response:
    """Validate provider credentials and return regions."""
    provider_id = request.path_params["provider"]
    provider = PROVIDERS.get(provider_id)

    if not provider:
        return JSONResponse({"valid": False, "error": "Unknown provider"}, status_code=404)

    # Get credentials from form
    form_data = await request.form()
    credentials = {field.name: form_data.get(field.name, "") for field in provider.fields}

    # Validate credentials
    result = await validate_credentials(provider_id, credentials)

    if not result.valid:
        return templates.TemplateResponse(
            request,
            "partials/validation_error.html",
            {"error": result.error},
            status_code=400,
        )

    # Return regions partial
    return templates.TemplateResponse(
        request,
        "partials/regions.html",
        {
            "provider": provider,
            "regions": result.regions or [],
            "credentials": credentials,
        },
    )


async def start_deploy(request: Request) -> Response:
    """Start a deployment."""
    form_data = await request.form()

    provider_id = form_data.get("provider", "")
    if not provider_id or provider_id not in PROVIDERS:
        return JSONResponse({"error": "Invalid provider"}, status_code=400)

    provider = PROVIDERS[provider_id]

    # Extract credentials
    credentials = {field.name: form_data.get(field.name, "") for field in provider.fields}

    # Extract config
    users_raw = form_data.get("users", "phone,laptop,desktop")
    users = [u.strip() for u in str(users_raw).split(",") if u.strip()]

    config = {
        "server_name": form_data.get("server_name", "algo"),
        "region": form_data.get("region", provider.default_region),
        "users": users,
        "wireguard_enabled": form_data.get("wireguard_enabled") == "on",
        "ipsec_enabled": form_data.get("ipsec_enabled") == "on",
        "dns_adblocking": form_data.get("dns_adblocking") == "on",
        "ssh_tunneling": form_data.get("ssh_tunneling") == "on",
        "ondemand_cellular": form_data.get("ondemand_cellular") == "on",
        "ondemand_wifi": form_data.get("ondemand_wifi") == "on",
        "store_pki": form_data.get("store_pki") == "on",
    }

    # Create session
    session = await sessions.create(
        provider=provider_id,
        credentials=credentials,
        config=config,
    )

    # Return redirect to deploy page via HX-Redirect header
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = f"/deploy/{session.id}"
    return response


async def deploy_stream(request: Request) -> Response:
    """SSE endpoint for deployment progress."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    async def event_generator():
        """Generate SSE events from playbook output."""
        try:
            async for line in run_playbook(session):
                # Send each line as an SSE event
                yield {
                    "event": "output",
                    "data": line,
                }

            # Send final status
            yield {
                "event": "complete",
                "data": session.status.value,
            }
        except asyncio.CancelledError:
            yield {
                "event": "complete",
                "data": "cancelled",
            }

    return EventSourceResponse(event_generator())


async def cancel_deploy(request: Request) -> Response:
    """Cancel a running deployment."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    success = await cancel_deployment(session)

    if success:
        return JSONResponse({"status": "cancelled"})
    return JSONResponse({"error": "Cannot cancel - deployment not running"}, status_code=400)


async def deploy_status(request: Request) -> Response:
    """Get deployment status."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    return JSONResponse(
        {
            "status": session.status.value,
            "exit_code": session.exit_code,
            "error": session.error,
            "config_path": session.config_path,
        }
    )


async def download_file(request: Request) -> Response:
    """Download a single config file."""
    session_id = request.path_params["session_id"]
    file_path = request.path_params["path"]

    session = await sessions.get(session_id)
    if not session or not session.config_path:
        return HTMLResponse("Not found", status_code=404)

    full_path = Path(session.config_path) / file_path
    if not full_path.exists() or not full_path.is_file():
        return HTMLResponse("File not found", status_code=404)

    # Security check: ensure path is within config directory
    try:
        full_path.resolve().relative_to(Path(session.config_path).resolve())
    except ValueError:
        return HTMLResponse("Access denied", status_code=403)

    return FileResponse(
        full_path,
        filename=full_path.name,
        media_type="application/octet-stream",
    )


async def download_zip(request: Request) -> Response:
    """Download all config files as a ZIP."""
    session_id = request.path_params["session_id"]
    session = await sessions.get(session_id)

    if not session or not session.config_path:
        return HTMLResponse("Not found", status_code=404)

    config_dir = Path(session.config_path)
    if not config_dir.exists():
        return HTMLResponse("Config directory not found", status_code=404)

    # Create ZIP in memory
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in config_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(config_dir)
                zf.write(file_path, arcname)

    buffer.seek(0)
    server_name = session.config.get("server_name", "algo")

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{server_name}-configs.zip"',
        },
    )


# === Application ===


routes = [
    # Pages
    Route("/", endpoint=index, methods=["GET"]),
    Route("/deploy/{session_id}", endpoint=deploy_page, methods=["GET"]),
    Route("/configs/{session_id}", endpoint=success_page, methods=["GET"]),
    # API - Provider
    Route("/providers/{provider}/form", endpoint=provider_form, methods=["GET"]),
    Route("/providers/{provider}/validate", endpoint=validate_provider, methods=["POST"]),
    # API - Deploy
    Route("/deploy", endpoint=start_deploy, methods=["POST"]),
    Route("/deploy/{session_id}/stream", endpoint=deploy_stream, methods=["GET"]),
    Route("/deploy/{session_id}/cancel", endpoint=cancel_deploy, methods=["POST"]),
    Route("/deploy/{session_id}/status", endpoint=deploy_status, methods=["GET"]),
    # API - Downloads
    Route("/configs/{session_id}/files/{path:path}", endpoint=download_file, methods=["GET"]),
    Route("/configs/{session_id}/zip", endpoint=download_zip, methods=["GET"]),
    # Static files
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"),
]

app = Starlette(routes=routes, debug=os.environ.get("DEBUG", "").lower() == "true")
