#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_config_dir, get_repo_root


PYTHON_PACKAGES = [
    ["opencv-python-headless", "numpy"],
    ["mediapipe"],
    ["pytesseract"],
    ["faster-whisper"],
]


def _run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


def _print_dependency_help(binary_name: str) -> None:
    install_map = {
        "ffmpeg": {
            "darwin": "brew install ffmpeg",
            "linux": "sudo apt-get install -y ffmpeg",
            "win32": "winget install Gyan.FFmpeg",
        },
        "tesseract": {
            "darwin": "brew install tesseract tesseract-lang",
            "linux": "sudo apt-get install -y tesseract-ocr tesseract-ocr-jpn",
            "win32": "winget install UB-Mannheim.TesseractOCR",
        },
    }
    command = install_map.get(binary_name, {}).get(sys.platform)
    if command:
        print(f"  Install example: {command}")
    else:
        print(f"  Install '{binary_name}' with your system package manager.")


def main() -> int:
    repo_root = get_repo_root()
    template_dir = repo_root / ".agent" / "skills" / "viral-template-generator" / "template"
    flag_dir = get_config_dir("viral-template-generator")
    flag_path = flag_dir / ".setup_done"

    print("viral-template-generator setup")

    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    for package_group in PYTHON_PACKAGES:
        _run([sys.executable, "-m", "pip", "install", *package_group])
        print(f"  installed: {' '.join(package_group)}")

    missing_required: list[str] = []
    missing_optional: list[str] = []
    for binary_name, required in (("ffmpeg", True), ("tesseract", False)):
        if shutil.which(binary_name):
            print(f"  detected system dependency: {binary_name}")
            continue
        if required:
            missing_required.append(binary_name)
        else:
            missing_optional.append(binary_name)

    if template_dir.exists():
        if shutil.which("npm") is None:
            print(
                "Required command was not found: npm. Install Node.js before using the Remotion template.",
                file=sys.stderr,
            )
            return 1
        _run(["npm", "install", "--quiet"], cwd=template_dir)
        print(f"  installed npm dependencies: {template_dir}")

    if missing_optional:
        print("Optional system dependencies are missing.")
        for binary_name in missing_optional:
            print(f"- {binary_name}")
            _print_dependency_help(binary_name)
        print("  OCR can be skipped with --skip-ocr until these are installed.")

    if missing_required:
        print("Required system dependencies are missing.", file=sys.stderr)
        for binary_name in missing_required:
            print(f"- {binary_name}", file=sys.stderr)
            _print_dependency_help(binary_name)
        return 1

    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_path.touch()
    print(f"Setup completed: {flag_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
