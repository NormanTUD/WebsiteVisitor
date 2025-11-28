@echo off
setlocal

:: Prüfen ob python3 verfügbar ist
where python >nul 2>&1
if errorlevel 1 (
  echo Python ist nicht installiert oder nicht im PATH.
  exit /b 1
)

:: Prüfen ob venv Modul vorhanden ist
python -c "import venv" 2>nul
if errorlevel 1 (
  echo Python venv Modul ist nicht installiert.
  exit /b 1
)

:: Prüfen ob pip verfügbar ist
python -m pip --version >nul 2>&1
if errorlevel 1 (
  echo pip ist nicht installiert.
  exit /b 1
)

set "VENV_DIR=%USERPROFILE%\website_visitor_venv"

:: Prüfen ob venv existiert, wenn nicht, erstellen
if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Erstelle virtual environment in %VENV_DIR%
  python -m venv "%VENV_DIR%"
)

:: Aktivieren der venv
call "%VENV_DIR%\Scripts\activate.bat"

:: Installieren der fehlenden Pakete
if exist requirements.txt (
  rem installiere nur Pakete, die noch nicht installiert sind
  python -m pip freeze > installed.txt
  findstr /v /g:installed.txt requirements.txt > to_install.txt

  for /f "usebackq delims=" %%a in ("to_install.txt") do (
    echo Installiere Paket %%a
    python -m pip install %%a
  )
  del installed.txt
  del to_install.txt
) else (
  echo Keine requirements.txt gefunden.
)

:: Python Script mit allen Argumenten starten
python website_visitor.py %*
