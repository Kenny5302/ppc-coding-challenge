.PHONY: run test lint typecheck audit check
run:        ; docker compose up --build
test:       ; docker compose --profile test run --rm --build tests
lint:       ; ruff check .
typecheck:  ; mypy app
audit:      ; pip-audit -r requirements.txt
check: lint typecheck
	pytest --cov=app
