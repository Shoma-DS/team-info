:; case "$(uname -s)" in Darwin*) bash "$(dirname "$0")/setup_mac.sh" "$@" ;; *) echo "This wrapper expects bash on macOS and cmd on Windows." >&2; exit 1 ;; esac; exit $?
@echo off
setlocal
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1" %*
)
exit /b %errorlevel%
