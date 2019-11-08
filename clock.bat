@echo off

SET PYTHONFILE=timeclock.py
SET PYTHONPATH=%~dp0\..\scripts\timeclock

REM Uses virtual env wrapper with the env "timeclock"
REM Activates env, calls script, deactivates env, and returns to cwd
workon timeclock & pushd %PYTHONPATH% & %PYTHONFILE% %* & deactivate & popd