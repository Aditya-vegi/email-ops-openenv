@echo off
REM OpenEnv CLI wrapper for Project Hack
cd /d "d:\project hack"
".venv\Scripts\python.exe" -m openenv.cli %*
