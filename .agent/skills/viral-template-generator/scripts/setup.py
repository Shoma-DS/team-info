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


# 必須 Python モジュール
PYTHON_MODULES_REQUIRED = [
    "cv2",
    "numpy",
    "pytesseract",
    "faster_whisper",
    "pykakasi",
]

# 任意 Python モジュール
PYTHON_MODULES_OPTIONAL = [
    "mediapipe",
    "librosa",
    "soundfile",
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

    missing_required_modules: list[str] = []
    missing_optional_modules: list[str] = []
    for module_name in PYTHON_MODULES_REQUIRED:
        try:
            __import__(module_name)
            print(f"  detected python module: {module_name}")
        except ImportError:
            missing_required_modules.append(module_name)

    for module_name in PYTHON_MODULES_OPTIONAL:
        try:
            __import__(module_name)
            print(f"  detected optional module: {module_name}")
        except ImportError:
            missing_optional_modules.append(module_name)

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
                "Optional command was not found: npm. Remotion template setup is skipped.",
            )
        else:
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

    if missing_required_modules:
        print("Required Python modules are missing.", file=sys.stderr)
        for module_name in missing_required_modules:
            print(f"- {module_name}", file=sys.stderr)
        print(
            "team_info_runtime.py build-remotion-python で Docker ランタイムを再ビルドしてください。",
            file=sys.stderr,
        )
        return 1

    if missing_optional_modules:
        print("Optional Python modules are missing.")
        for module_name in missing_optional_modules:
            print(f"- {module_name}")
        print(
            "必要なら setup/requirements.txt を更新して "
            "team_info_runtime.py build-remotion-python を実行してください。"
        )

    flag_dir.mkdir(parents=True, exist_ok=True)
    flag_path.touch()
    print(f"Setup completed: {flag_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
