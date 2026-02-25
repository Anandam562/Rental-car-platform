@echo off
REM Create static asset directories
mkdir static
mkdir static\css
mkdir static\js
mkdir static\images
mkdir static\uploads

REM Create CSS files
type nul > static\css\style.css
type nul > static\css\host.css
type nul > static\css\dashboard.css

REM Create JS files
type nul > static\js\main.js
type nul > static\js\host.js

echo Static asset directories and files created successfully.
pause
