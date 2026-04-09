@echo off
REM HeiBan - Build only (no upload)
setlocal
cd /d "%~dp0"

if not defined PYTHON set "PYTHON=python"

echo === HeiBan Build ===

echo [1/4] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
if exist heiban.egg-info rmdir /s /q heiban.egg-info

echo [2/4] Installing build tools...
%PYTHON% -m pip install --upgrade build -q

echo [3/4] Building package...
%PYTHON% -m build
if %errorlevel% neq 0 (echo Build failed! & exit /b 1)

echo [4/4] Checking package...
%PYTHON% -m twine check dist\*
if %errorlevel% neq 0 (echo Check failed! & exit /b 1)

echo.
echo Build complete! Files in dist/
dir /b dist\

echo === Done! ===
endlocal