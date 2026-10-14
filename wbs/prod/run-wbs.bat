@echo off
REM World Builder Studio — Textual TUI (build / play chooser)
cd /d "%~dp0"
python run-in-deck-host.py --in-console
if errorlevel 1 pause
