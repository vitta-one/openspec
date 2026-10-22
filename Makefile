# Desenvolvimento local: Reflex no host, apenas PostgreSQL em Docker.
.PHONY: dev admin db-only db-stop db-logs db-status

dev:
	@bash scripts/dev-local.sh dev

admin:
	@bash scripts/dev-local.sh admin

db-only:
	@bash scripts/dev-local.sh db-only

db-stop:
	@docker compose -p vitta-one-local --env-file .env.docker -f compose.dev.yaml stop db

db-logs:
	@docker compose -p vitta-one-local --env-file .env.docker -f compose.dev.yaml logs -f db

db-status:
	@docker compose -p vitta-one-local --env-file .env.docker -f compose.dev.yaml ps
