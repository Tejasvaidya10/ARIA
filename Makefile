.PHONY: lint format typecheck test test-service up down clean

lint:
	ruff check . && ruff format --check .

format:
	ruff format . && ruff check --fix .

typecheck:
	mypy services/

test:
	pytest services/ tests/

test-service:
	pytest services/$(SVC)/tests/ -v

up:
	docker compose up --build

down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; \
	true
