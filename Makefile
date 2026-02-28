.PHONY: up down ps revision upgrade

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

revision:
	@printf "Enter revision message: "; \
	read msg; \
	cd backend/app && \
	if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "Activating virtual environment..."; \
		. ../.venv/bin/activate; \
	fi && \
	uv run alembic revision --autogenerate -m "$$msg"

upgrade:
	cd backend/app && \
	if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "Activating virtual environment..."; \
		. ../.venv/bin/activate; \
	fi && \
	alembic upgrade head