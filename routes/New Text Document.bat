@echo off
REM Create the directory structure
mkdir user

REM Navigate into the directory
cd user

REM Create the Python files
echo.> __init__.py
echo.> dashboard.py
echo.> bookings.py
echo.> notifications.py

REM Done
echo Directory and files created successfully.
