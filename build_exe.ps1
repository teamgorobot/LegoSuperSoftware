# Build a portable Windows .exe with PyInstaller
# Run from repo root: .\build_exe.ps1

$VenvPath = ".venv"
$PythonExe = Join-Path $VenvPath "Scripts\\python.exe"

if (-not (Test-Path $PythonExe)) {
  python -m venv $VenvPath
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install PySide6 openai
if ($LASTEXITCODE -ne 0) {
  Write-Host "Failed to install core requirements (PySide6/openai). Aborting." -ForegroundColor Red
  exit 1
}
& $PythonExe -m pip install llama-cpp-python
if ($LASTEXITCODE -ne 0) {
  Write-Host "llama-cpp-python failed to build. Offline local models will be unavailable in the exe." -ForegroundColor Yellow
}
& $PythonExe -m pip install pyinstaller

# If you want offline/local AI in the .exe, install llama-cpp-python first:
# python -m pip install llama-cpp-python

$AppEntry = "app\main.py"
$Name = "LegoSuperSoftware"

& $PythonExe -m PyInstaller `
  --noconfirm `
  --onefile `
  --windowed `
  --name $Name `
  --hidden-import PySide6 `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  --collect-submodules PySide6 `
  --collect-all PySide6 `
  --collect-all shiboken6 `
  --collect-submodules openai `
  $AppEntry
if ($LASTEXITCODE -eq 0) {
  Write-Host "Build complete. Check the dist/ folder." -ForegroundColor Green
} else {
  Write-Host "Build failed. See errors above." -ForegroundColor Red
}
