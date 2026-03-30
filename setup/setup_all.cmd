:; case "$(uname -s)" in Darwin*) bash "$(dirname "$0")/setup_mac.sh" "$@" ;; *) echo "このラッパーは macOS では bash、Windows では cmd から使う前提です。" >&2; exit 1 ;; esac; exit $?
@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1" %*
exit /b %errorlevel%
