.PHONY: dev stop test lint build deploy

dev:
	docker compose up --build

stop:
	docker compose down

test:
	docker compose run --rm backend pytest -v

lint:
	docker compose run --rm backend ruff check app/
	cd frontend && npm run lint

build:
	docker compose build

challenges:
	docker compose run --rm backend python -m app.services.challenge_loader --rebuild

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
