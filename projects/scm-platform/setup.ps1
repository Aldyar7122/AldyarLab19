$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\Scripts\python.exe -m pip install -e . --no-build-isolation
