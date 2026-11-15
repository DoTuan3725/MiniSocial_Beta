@echo off
chcp 65001 >nul
echo ========================================================
echo   KHOI DONG MANG XA HOI MINI (DOCKER COMPOSE - DEV)
echo ========================================================
cd /d "%~dp0"
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Da tao .env tu .env.example
)
docker compose up -d --build
echo.
echo   Tao du lieu demo (chi can lan dau):
echo     docker compose exec backend python manage.py seed_demo
echo.
echo   Web:      http://localhost
echo   Swagger:  http://localhost/api/v1/docs/
echo   MinIO:    http://localhost:9001
echo ========================================================
pause
