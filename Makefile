# Lệnh tắt cho Linux/macOS (Windows dùng run_docker.bat)
up:        ; docker compose up -d --build
down:      ; docker compose down
logs:      ; docker compose logs -f backend worker
seed:      ; docker compose exec backend python manage.py seed_demo
migrate:   ; docker compose exec backend python manage.py migrate
test:      ; cd backend && DB_ENGINE=sqlite pytest --cov
lint:      ; cd backend && flake8 && black --check . && isort --check-only . && lint-imports
reset-db:  ; docker compose down -v
