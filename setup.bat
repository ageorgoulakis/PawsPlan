@echo off

REM Download and install GTK3 runtime
set "GTK_INSTALLER_URL=https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
set "GTK_INSTALLER=gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"

REM Download GTK3 installer
echo Downloading GTK3 runtime...
curl -L -o %GTK_INSTALLER% %GTK_INSTALLER_URL%

REM Install GTK3 runtime
echo Installing GTK3 runtime...
start /wait %GTK_INSTALLER% /S /norestart

REM Set GTK environment variable (adjust the path as necessary)
set GTK_PATH=C:\Program Files\GTK3-Runtime Win64\bin
set PATH=%GTK_PATH%;%PATH%

REM Install WeasyPrint and other dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Installation completed.
pause
