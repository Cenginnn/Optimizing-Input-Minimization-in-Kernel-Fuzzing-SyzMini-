#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/configs/v515.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

: "${KERNEL_DIR:?Set KERNEL_DIR in configs/v515.env}"
: "${IMAGE_DIR:?Set IMAGE_DIR in configs/v515.env}"
: "${SYZKALLER_DIR:=${ROOT}/syzmini}"
: "${INFLUENCE_FILE:=${ROOT}/influencev5.15.txt}"

for path in "$KERNEL_DIR/vmlinux" "$KERNEL_DIR/arch/x86/boot/bzImage" \
            "$IMAGE_DIR/trixie.img" "$IMAGE_DIR/trixie.id_rsa" \
            "$SYZKALLER_DIR/bin/syz-manager" "$INFLUENCE_FILE"; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: required file not found: $path" >&2
    exit 1
  fi
done

if [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then
  echo "ERROR: /dev/kvm is not readable and writable by the current user." >&2
  exit 1
fi

printf '%s\n' '=== Environment ==='
printf 'Date:       '; date --iso-8601=seconds
printf 'OS:         '; . /etc/os-release; echo "${PRETTY_NAME:-unknown}"
printf 'Host:       '; uname -a
printf 'Compiler:   '; gcc --version | head -n 1
printf 'Go:         '; go version
printf 'QEMU:       '; qemu-system-x86_64 --version | head -n 1
printf 'Git commit: '; git -C "$ROOT" rev-parse HEAD
printf 'Kernel dir: %s\n' "$(realpath "$KERNEL_DIR")"
printf 'Image dir:  %s\n' "$(realpath "$IMAGE_DIR")"
printf 'SyzMini:    %s\n' "$(realpath "$SYZKALLER_DIR")"
printf 'Influence:  %s\n' "$(realpath "$INFLUENCE_FILE")"
printf 'KVM:        readable/writable\n'
printf 'Kernel config: '
grep -E '^(CONFIG_KCOV|CONFIG_KASAN|CONFIG_DEBUG_INFO|CONFIG_E1000|CONFIG_E1000E|CONFIG_VIRTIO_NET)=' "$KERNEL_DIR/.config" || true
