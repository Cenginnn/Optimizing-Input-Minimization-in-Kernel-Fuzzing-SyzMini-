#!/usr/bin/env python3
"""Generate a machine-local SyzMini manager config from the tracked template."""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "configs" / "v515.template.json"
OUTPUT = REPO_ROOT / "configs" / "generated" / "v515.cfg"


def required_path(name: str, default: str | None = None) -> Path:
    value = os.environ.get(name, default)
    if not value:
        raise SystemExit(f"Missing {name}. Set it in configs/v515.env.")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"{name} does not exist: {path}")
    return path


def positive_int(name: str, default: str) -> int:
    value = int(os.environ.get(name, default))
    if value <= 0:
        raise SystemExit(f"{name} must be greater than zero")
    return value


def main() -> None:
    kernel_dir = required_path("KERNEL_DIR")
    image_dir = required_path("IMAGE_DIR")
    syzkaller_dir = required_path("SYZKALLER_DIR", str(REPO_ROOT / "syzmini"))
    image_file = image_dir / "trixie.img"
    ssh_key = image_dir / "trixie.id_rsa"
    kernel_image = kernel_dir / "arch" / "x86" / "boot" / "bzImage"
    vmlinux = kernel_dir / "vmlinux"

    for path in (image_file, ssh_key, kernel_image, vmlinux):
        if not path.is_file():
            raise SystemExit(f"Required file not found: {path}")

    workdir = Path(os.environ.get("WORKDIR", str(REPO_ROOT / "workdir"))).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    values = {
        "@@HTTP_ADDR@@": os.environ.get("HTTP_ADDR", "127.0.0.1:56741"),
        "@@WORKDIR@@": str(workdir),
        "@@KERNEL_DIR@@": str(kernel_dir),
        "@@IMAGE_FILE@@": str(image_file),
        "@@SSH_KEY@@": str(ssh_key),
        "@@SYZKALLER_DIR@@": str(syzkaller_dir),
        "@@PROCS@@": str(positive_int("PROCS", "8")),
        "@@VM_COUNT@@": str(positive_int("VM_COUNT", "4")),
        "@@KERNEL_IMAGE@@": str(kernel_image),
        "@@VM_CPU@@": str(positive_int("VM_CPU", "2")),
        "@@VM_MEM@@": str(positive_int("VM_MEM", "2048")),
    }
    rendered = TEMPLATE.read_text(encoding="utf-8")
    for token, value in values.items():
        rendered = rendered.replace(token, value)
    config = json.loads(rendered)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Generated: {OUTPUT}")
    print(f"Kernel:    {kernel_image}")
    print(f"Image:     {image_file}")
    print(f"Workdir:   {workdir}")


if __name__ == "__main__":
    main()
