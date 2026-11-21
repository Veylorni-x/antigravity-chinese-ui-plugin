@echo off
setlocal
chcp 65001 >nul
set "SCRIPT=%~dp0..\skills\localize-ui\scripts\patch.py"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo 未找到 Python。请先安装 Python 3.8 或更新版本。
  pause
  exit /b 1
)
%PY% -X utf8 "%SCRIPT%" restore
set "RC=%ERRORLEVEL%"
pause
exit /b %RC%
