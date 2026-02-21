@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM EyeCare App3 - Auto-detect Wi-Fi IPv4, update Flutter API URL,
REM then start the backend.
REM
REM What it does:
REM  1) Detects the current local IPv4 used for the default route
REM  2) Updates lib\services\api.dart (ApiService._baseUrl)
REM  3) Starts eyecare_backend in dev mode
REM
REM Run this whenever you switch Wi-Fi networks.
REM ============================================================

set PORT=5000
set API_DART=lib\services\api.dart

echo.
echo ================================================
echo  Auto IP Update + Start Backend (App3)
echo ================================================
echo.

REM --- Detect IP (uses interface with default route) ---
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1; $ifIndex = $route.InterfaceIndex; $ip = Get-NetIPAddress -InterfaceIndex $ifIndex -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.254*' -and $_.IPAddress -ne '127.0.0.1' } | Select-Object -First 1 -ExpandProperty IPAddress; if (-not $ip) { exit 1 } ; Write-Output $ip"`
) do set LOCAL_IP=%%I

if "%LOCAL_IP%"=="" (
  echo ERROR: Could not detect a local IPv4 address.
  echo - Make sure you are connected to Wi-Fi.
  echo - If you use Ethernet, this script will pick that network.
  echo.
  pause
  exit /b 1
)

echo Detected IP: %LOCAL_IP%
set BASE_URL=http://%LOCAL_IP%:%PORT%
echo New base URL: %BASE_URL%

REM --- Patch Flutter API baseUrl in api.dart ---
if not exist "%API_DART%" (
  echo ERROR: Could not find %API_DART%
  echo Make sure you run this from the app3 folder.
  echo.
  pause
  exit /b 1
)

echo.
echo Updating %API_DART% ...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$path = '%API_DART%';" ^
  "$base = '%BASE_URL%';" ^
  "$content = Get-Content -Raw -Path $path;" ^
  "$pattern = ""static\s+String\s+_baseUrl\s*=\s*'http://[^']+';"";" ^
  "$replacement = ""static String _baseUrl = '$base';"";" ^
  "$updated = [Regex]::Replace($content, $pattern, $replacement);" ^
  "if ($updated -eq $content) { Write-Host 'WARNING: Pattern not found; no changes made.' }" ^
  "Set-Content -Path $path -Value $updated -Encoding UTF8;" ^
  "Write-Host 'OK: api.dart updated.'"

if errorlevel 1 (
  echo ERROR: Failed to update %API_DART%
  echo.
  pause
  exit /b 1
)

REM --- Start backend ---
echo.
echo Starting backend (eyecare_backend) ...

echo NOTE: Keep this window open while the server runs.

echo.
pushd eyecare_backend
call START_DEV.bat
popd

endlocal
