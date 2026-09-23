.PHONY: up down logs seed burst migrate

up:
	docker compose up --build -d
	@echo "waiting for postgres..."
	@until docker compose exec -T postgres pg_isready -U haulwise >/dev/null 2>&1; do sleep 1; done
	$(MAKE) migrate
	$(MAKE) seed
	@echo "Haulwise is up: web http://localhost:3000  api http://localhost:8000"

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm -T api python -m db_migrate

seed:
	docker compose run --rm -T api python -m db_seed

burst:
	docker compose exec -T simulator python -m burst
