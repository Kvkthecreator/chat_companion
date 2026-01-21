# API Makefile for development and testing

.PHONY: help install migrate test smoke-test lint-imports format run

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make migrate     - Run database migrations"
	@echo "  make test        - Run unit tests"
	@echo "  make smoke-test  - Run smoke tests (requires running server)"
	@echo "  make lint-imports - Check Python imports"
	@echo "  make run         - Run development server"

install:
	pip install -r requirements.txt
	pip install PyMuPDF>=1.24.0

migrate:
	python run_migrations.py

test:
	PYTHONPATH=src pytest -q

smoke-test:
	./smoke_tests.sh

lint-imports:
	python scripts/compile_all.py

run:
	uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Development helpers
check-env:
	@echo "Checking environment variables..."
	@test -n "$$ALLOWED_PUBLIC_BASE" || (echo "❌ ALLOWED_PUBLIC_BASE not set" && exit 1)
	@test -n "$$DATABASE_URL" || (echo "❌ DATABASE_URL not set" && exit 1)
	@echo "✅ Environment variables OK"

dev: check-env migrate run
