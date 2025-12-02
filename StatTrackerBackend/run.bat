@echo off
REM Run script for Baseball Stats API (Windows)

echo ============================================================
echo Baseball Stats API - Lovable Frontend Integration
echo ============================================================
echo.
echo EXACT URLs for Lovable to call:
echo   POST http://localhost:8000/upload
echo   GET  http://localhost:8000/totals
echo   GET  http://localhost:8000/games
echo.
echo ============================================================
echo Starting server on http://0.0.0.0:8000
echo ============================================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000

