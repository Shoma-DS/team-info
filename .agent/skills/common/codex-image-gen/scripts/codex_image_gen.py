#!/usr/bin/env python3
# Codex サブスクリプション（ChatGPT Plus）経由で GPT Image 2 を使って画像を生成するラッパー。
# codex exec + IPC ソケットを通じて Codex.app の認証を使い、API キー不要で動作する。
# 使い方: python3 codex_image_gen.py "<プロンプト>" "<出力パス>.png" ["1024x1024"]

import subprocess
import sys
import os
import glob
import shutil


VALID_SIZES = {"1024x1024", "1792x1024", "1024x1792"}


def find_ipc_socket() -> str | None:
    uid = os.getuid()
    # /var/folders/<x>/<hash>/T/codex-ipc/ipc-<uid>.sock (2 levels deep)
    for pattern in [
        f"/var/folders/*/*/T/codex-ipc/ipc-{uid}.sock",
        f"/var/folders/*/T/codex-ipc/ipc-{uid}.sock",
    ]:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[0]
    return None


def check_codex_app_running() -> bool:
    result = subprocess.run(["pgrep", "-x", "Codex"], capture_output=True)
    return result.returncode == 0


def codex_cli_path() -> str:
    bundled = "/Applications/Codex.app/Contents/Resources/codex"
    if os.path.isfile(bundled):
        return bundled
    found = shutil.which("codex")
    if found:
        return found
    print("Error: codex CLI が見つかりません。`npm install -g @openai/codex` でインストールしてください。", file=sys.stderr)
    sys.exit(1)


def generate_image(prompt: str, output_path: str, size: str = "1024x1024") -> None:
    if size not in VALID_SIZES:
        print(f"Error: サイズ指定が不正です。{VALID_SIZES} のどれかを指定してください。", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if not check_codex_app_running():
        print("Error: Codex.app が起動していません。/Applications/Codex.app を起動してから再実行してください。", file=sys.stderr)
        sys.exit(1)

    sock = find_ipc_socket()
    if not sock:
        print("Error: Codex.app の IPC ソケットが見つかりません。Codex.app が完全に起動するまで少し待ってから再実行してください。", file=sys.stderr)
        sys.exit(1)

    codex_prompt = (
        f"GPT Image 2 で次の画像を生成し、{output_path} にPNG形式で保存してください。\n"
        f"サイズ: {size}\n"
        f"プロンプト: {prompt}\n\n"
        f"画像生成ツールを呼び出した後、生成された画像データを {output_path} へ保存するコードを実行してください。"
    )

    cli = codex_cli_path()
    cmd = [cli, "--remote", f"unix://{sock}", "exec", codex_prompt]

    print(f"Codex 経由で画像を生成中... (サイズ: {size})", flush=True)
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"Error: codex exec が失敗しました（終了コード {result.returncode}）。", file=sys.stderr)
        print("Codex.app のインタラクティブモードで手動実行することも検討してください。", file=sys.stderr)
        sys.exit(result.returncode)

    if os.path.isfile(output_path):
        print(f"完了: {output_path}")
    else:
        print(f"Warning: codex は正常終了しましたが、{output_path} が見つかりません。", file=sys.stderr)
        print("Codex.app のセッションを確認するか、インタラクティブモードで保存してください。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使い方: python3 codex_image_gen.py \"<プロンプト>\" \"<出力パス>.png\" [\"1024x1024\"|\"1792x1024\"|\"1024x1792\"]")
        sys.exit(1)

    prompt_arg = sys.argv[1]
    output_arg = sys.argv[2]
    size_arg = sys.argv[3] if len(sys.argv) > 3 else "1024x1024"

    generate_image(prompt_arg, output_arg, size_arg)
