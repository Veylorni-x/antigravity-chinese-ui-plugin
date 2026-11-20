@echo off
setlocal
chcp 65001 >nul
python -X utf8 "%~dp0..\skills\localize-ui\scripts\patch.py" install
pause
