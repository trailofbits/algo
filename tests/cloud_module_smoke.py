"""Load cloud SDKs in a fresh process, matching Ansible's collection startup."""

import importlib
import io
import json
import sys
import warnings
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import yaml
from ansible.module_utils import basic
from ansible.plugins.loader import init_plugin_loader


def check_collection(module, name: str) -> None:
    """Verify that module resolution selected the collection pinned by Algo."""
    root = Path(__file__).resolve().parents[1]
    requirements = yaml.safe_load((root / "requirements.yml").read_text())["collections"]
    version = next(item["version"].lstrip("=") for item in requirements if item["name"] == name)
    manifest = Path(module.__file__).parents[2] / "MANIFEST.json"
    assert json.loads(manifest.read_text())["collection_info"]["version"] == version


def check_azure_imports() -> None:
    """Import deployment and deletion modules and instantiate the used SDK operation groups."""
    prefix = "ansible_collections.azure.azcollection.plugins."
    common = importlib.import_module(prefix + "module_utils.azure_rm_common")
    check_collection(common, "azure.azcollection")
    assert common.AZURE_IMPORT_ERROR is None, common.AZURE_IMPORT_ERROR
    for name in ("azure_rm_deployment", "azure_rm_resource_info", "azure_rm_resourcegroup"):
        importlib.import_module(prefix + "modules." + name)
    from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
    from azure.mgmt.resource.locks import ManagementLockClient

    credential = object()
    assert ResourceManagementClient(credential, "test").deployments
    assert SubscriptionClient(credential).subscriptions
    assert ManagementLockClient(credential, "test").management_locks


def check_linode_imports() -> None:
    """Import both provisioning modules, including their specdoc dependency."""
    for name in ("stackscript", "instance"):
        module = importlib.import_module("ansible_collections.linode.cloud.plugins.modules." + name)
        check_collection(module, "linode.cloud")


def check_locations(locations: list[dict]) -> None:
    """Execute the real Azure resource module with only its HTTP query replaced."""
    module = importlib.import_module(
        "ansible_collections.azure.azcollection.plugins.modules.azure_rm_resource_info",
    )
    check_collection(module, "azure.azcollection")
    response = SimpleNamespace(
        status_code=200,
        body=lambda: json.dumps({"value": locations}).encode(),
    )
    query = Mock(return_value=response)
    arguments = {
        "url": "/subscriptions/test-subscription/locations",
        "api_version": "2022-12-01",
        "subscription_id": "test-subscription",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "tenant": "00000000-0000-0000-0000-000000000002",
        "secret": "test-only-secret",
    }
    basic._ANSIBLE_ARGS = json.dumps({"ANSIBLE_MODULE_ARGS": arguments}).encode()
    basic._ANSIBLE_PROFILE = "legacy"
    output = io.StringIO()
    with patch.object(module.GenericRestClient, "query", query), redirect_stdout(output):
        try:
            module.AzureRMResourceInfo()
        except SystemExit as result:
            assert result.code == 0, output.getvalue()
        else:
            raise AssertionError("Ansible module did not return its result")
    # The collection unwraps nonempty arrays; an empty list retains the response object.
    assert json.loads(output.getvalue())["response"] == (locations or [{"value": []}])
    assert query.call_args.args[:3] == (
        "/subscriptions/test-subscription/locations",
        "GET",
        {"api-version": "2022-12-01"},
    )


if __name__ == "__main__":
    # The upstream Batch SDK contains invalid escapes in two docstrings.
    warnings.filterwarnings(
        "ignore",
        "invalid escape sequence",
        DeprecationWarning,
        r"azure\.mgmt\.batch\.models\._models_py3",
    )
    init_plugin_loader()
    match sys.argv[1]:
        case "azure":
            check_azure_imports()
        case "linode":
            check_linode_imports()
        case "locations":
            check_locations(json.loads(sys.argv[2]))
        case other:
            raise ValueError(f"Unknown cloud smoke check: {other}")
