#!/usr/bin/python
"""Publish a private WireGuard QR image when its rendered content changes."""

import io
import os
import stat
from pathlib import Path

import segno
from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    """Render in memory, preserve unchanged images and replace damaged ones atomically."""
    module = AnsibleModule(
        argument_spec={
            "config_path": {"type": "path", "required": True},
            "image_path": {"type": "path", "required": True},
        },
        supports_check_mode=True,
    )
    target = Path(module.params["image_path"])
    os.umask(0o077)
    try:
        source = Path(module.params["config_path"]).read_text()
        image = io.BytesIO()
        segno.make(source, micro=False).save(image, kind="png", scale=5)
        try:
            mode = target.lstat().st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None and not stat.S_ISREG(mode):
            module.fail_json(msg=f"Expected a regular QR image file at {target}")
        changed = mode is None or target.read_bytes() != image.getvalue()
        if changed and not module.check_mode:
            temporary = Path(module.tmpdir) / "wireguard.png"
            temporary.write_bytes(image.getvalue())
            module.atomic_move(str(temporary), str(target), keep_dest_attrs=False)
        if mode is not None and stat.S_IMODE(mode) != 0o600:
            if not module.check_mode:
                target.chmod(0o600)
            changed = True
    except (OSError, ValueError) as error:
        module.fail_json(msg=f"Cannot generate the WireGuard QR image at {target}: {error}")
    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
