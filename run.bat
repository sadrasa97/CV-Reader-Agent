@echo off
REM CV Reader Agent Pipeline - Startup Script for Windows
REM Prerequisites: Docker Desktop for Windows, Docker Compose

echo.
echo 🚀 Starting CV Reader Agent Pipeline...
echo.

REM Copy .env.example to .env if it doesn't exist
if not exist .env (
    echo 📋 Creating .env from .env.example...
    copy .env.example .env
    echo ✅ .env created. Edit it if needed.
    echo.
)

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop for Windows first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo 🐳 Docker is installed. Starting services...
echo.

REM Start services
docker-compose up --build

echo.
echo ✅ Services started successfully!
echo.
echo 📌 Access the application:
echo    - Streamlit UI: http://localhost:8501
echo    - FastAPI Docs: http://localhost:8000/docs
echo    - API Health: http://localhost:8000/health
echo.
echo 🛑 To stop the services, press Ctrl+C
pause
