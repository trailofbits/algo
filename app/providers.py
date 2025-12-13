"""Cloud provider credential schemas and validation."""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ProviderField:
    """A credential field for a cloud provider."""

    name: str
    label: str
    field_type: str = "password"  # password, text, file
    placeholder: str = ""
    help_url: str = ""


@dataclass
class Provider:
    """Cloud provider configuration."""

    id: str
    name: str
    fields: list[ProviderField]
    regions_api: str = ""
    default_region: str = ""


# Provider definitions for MVP (simple token auth providers)
PROVIDERS: dict[str, Provider] = {
    "digitalocean": Provider(
        id="digitalocean",
        name="DigitalOcean",
        fields=[
            ProviderField(
                name="do_token",
                label="API Token",
                field_type="password",
                placeholder="Enter your DigitalOcean API token",
                help_url="https://cloud.digitalocean.com/settings/api/tokens",
            ),
        ],
        regions_api="https://api.digitalocean.com/v2/regions",
        default_region="nyc3",
    ),
    "hetzner": Provider(
        id="hetzner",
        name="Hetzner Cloud",
        fields=[
            ProviderField(
                name="hcloud_token",
                label="API Token",
                field_type="password",
                placeholder="Enter your Hetzner Cloud API token",
                help_url="https://console.hetzner.cloud/projects",
            ),
        ],
        regions_api="https://api.hetzner.cloud/v1/datacenters",
        default_region="nbg1",
    ),
    "linode": Provider(
        id="linode",
        name="Linode",
        fields=[
            ProviderField(
                name="linode_token",
                label="API Token",
                field_type="password",
                placeholder="Enter your Linode API token",
                help_url="https://cloud.linode.com/profile/tokens",
            ),
        ],
        regions_api="https://api.linode.com/v4/regions",
        default_region="us-east",
    ),
    "vultr": Provider(
        id="vultr",
        name="Vultr",
        fields=[
            ProviderField(
                name="vultr_api_key",
                label="API Key",
                field_type="password",
                placeholder="Enter your Vultr API key",
                help_url="https://my.vultr.com/settings/#settingsapi",
            ),
        ],
        regions_api="https://api.vultr.com/v2/regions",
        default_region="ewr",
    ),
}


@dataclass
class Region:
    """A cloud provider region."""

    id: str
    name: str
    available: bool = True


@dataclass
class ValidationResult:
    """Result of credential validation."""

    valid: bool
    error: str = ""
    regions: list[Region] | None = None


async def validate_digitalocean(token: str) -> ValidationResult:
    """Validate DigitalOcean API token and fetch regions."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                "https://api.digitalocean.com/v2/regions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                return ValidationResult(
                    valid=False,
                    error="Invalid or expired API token. Please check your token and try again.",
                )
            if response.status_code == 403:
                return ValidationResult(
                    valid=False,
                    error="Token lacks required permissions. Ensure it has Read and Write scopes.",
                )
            if response.status_code == 429:
                return ValidationResult(
                    valid=False,
                    error="Rate limit exceeded. Please wait a few minutes and try again.",
                )
            if response.status_code != 200:
                return ValidationResult(
                    valid=False,
                    error=f"API error (HTTP {response.status_code}). Please try again later.",
                )

            data = response.json()
            regions = [
                Region(id=r["slug"], name=r["name"], available=r.get("available", True))
                for r in data.get("regions", [])
                if r.get("available", True)
            ]
            regions.sort(key=lambda r: r.id)

            return ValidationResult(valid=True, regions=regions)

        except httpx.TimeoutException:
            return ValidationResult(
                valid=False,
                error="Connection timed out. Please check your internet connection.",
            )
        except httpx.RequestError as e:
            return ValidationResult(valid=False, error=f"Connection error: {e!s}")


async def validate_hetzner(token: str) -> ValidationResult:
    """Validate Hetzner Cloud API token and fetch datacenters."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                "https://api.hetzner.cloud/v1/datacenters",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                return ValidationResult(
                    valid=False,
                    error="Invalid or expired API token. Please check your token.",
                )
            if response.status_code != 200:
                return ValidationResult(
                    valid=False,
                    error=f"API error (HTTP {response.status_code}). Please try again.",
                )

            data = response.json()
            regions = [
                Region(
                    id=dc["name"],
                    name=f"{dc['location']['city']} ({dc['description']})",
                    available=True,
                )
                for dc in data.get("datacenters", [])
            ]
            regions.sort(key=lambda r: r.id)

            return ValidationResult(valid=True, regions=regions)

        except httpx.TimeoutException:
            return ValidationResult(
                valid=False,
                error="Connection timed out. Please check your internet connection.",
            )
        except httpx.RequestError as e:
            return ValidationResult(valid=False, error=f"Connection error: {e!s}")


async def validate_linode(token: str) -> ValidationResult:
    """Validate Linode API token and fetch regions."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                "https://api.linode.com/v4/regions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                return ValidationResult(
                    valid=False,
                    error="Invalid or expired API token. Please check your token.",
                )
            if response.status_code != 200:
                return ValidationResult(
                    valid=False,
                    error=f"API error (HTTP {response.status_code}). Please try again.",
                )

            data = response.json()
            regions = [
                Region(
                    id=r["id"],
                    name=f"{r['label']} ({r['country'].upper()})",
                    available=r.get("status") == "ok",
                )
                for r in data.get("data", [])
                if r.get("status") == "ok"
            ]
            regions.sort(key=lambda r: r.id)

            return ValidationResult(valid=True, regions=regions)

        except httpx.TimeoutException:
            return ValidationResult(
                valid=False,
                error="Connection timed out. Please check your internet connection.",
            )
        except httpx.RequestError as e:
            return ValidationResult(valid=False, error=f"Connection error: {e!s}")


async def validate_vultr(api_key: str) -> ValidationResult:
    """Validate Vultr API key and fetch regions."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                "https://api.vultr.com/v2/regions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                return ValidationResult(
                    valid=False,
                    error="Invalid API key. Please check your key and try again.",
                )
            if response.status_code != 200:
                return ValidationResult(
                    valid=False,
                    error=f"API error (HTTP {response.status_code}). Please try again.",
                )

            data = response.json()
            regions = [
                Region(
                    id=r["id"],
                    name=f"{r['city']} ({r['country']})",
                    available=True,
                )
                for r in data.get("regions", [])
            ]
            regions.sort(key=lambda r: r.id)

            return ValidationResult(valid=True, regions=regions)

        except httpx.TimeoutException:
            return ValidationResult(
                valid=False,
                error="Connection timed out. Please check your internet connection.",
            )
        except httpx.RequestError as e:
            return ValidationResult(valid=False, error=f"Connection error: {e!s}")


async def validate_credentials(provider_id: str, credentials: dict[str, Any]) -> ValidationResult:
    """Validate credentials for a given provider."""
    if provider_id == "digitalocean":
        token = credentials.get("do_token", "")
        if not token:
            return ValidationResult(valid=False, error="API token is required")
        return await validate_digitalocean(token)

    if provider_id == "hetzner":
        token = credentials.get("hcloud_token", "")
        if not token:
            return ValidationResult(valid=False, error="API token is required")
        return await validate_hetzner(token)

    if provider_id == "linode":
        token = credentials.get("linode_token", "")
        if not token:
            return ValidationResult(valid=False, error="API token is required")
        return await validate_linode(token)

    if provider_id == "vultr":
        api_key = credentials.get("vultr_api_key", "")
        if not api_key:
            return ValidationResult(valid=False, error="API key is required")
        return await validate_vultr(api_key)

    return ValidationResult(valid=False, error=f"Unknown provider: {provider_id}")
