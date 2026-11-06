# Conveniences only: `docker compose up --build` is all a clean machine needs.
FILE ?= data/tickets.csv
API ?= http://localhost:8000
OPERATOR_USERNAME ?= operator
OPERATOR_PASSWORD ?= operator

.PHONY: up down test import eval bench

up:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm --build tests

import:
	@TOKEN=$$(curl -fsS -H 'Content-Type: application/json' \
		-d '{"username":"$(OPERATOR_USERNAME)","password":"$(OPERATOR_PASSWORD)"}' \
		$(API)/api/auth/login | sed 's/.*"access_token":"\([^"]*\)".*/\1/') && \
	curl -fsS -H "Authorization: Bearer $$TOKEN" \
		-F "file=@$(FILE);type=text/csv" $(API)/api/imports
	@echo

# Stop the worker first: the model cannot serve both without slowing down.
eval:
	docker compose --profile tools run --rm -T eval > eval/report.md

bench:
	docker compose --profile tools run --rm -T eval python -m app.evaluation bench > eval/bench.md
