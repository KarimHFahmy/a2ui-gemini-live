# Adaptive Advisory Experiences — developer entry points.
#
#   make install     install both toolchains
#   make dev         run backend and frontend with hot reload
#   make test        backend tests + frontend typecheck + catalog check
#   make build       build the SPA into backend/static
#   make deploy      build and deploy to Cloud Run

SHELL := /bin/bash
PY ?= python3
REGION ?= europe-west4
SERVICE ?= adaptive-advisory
PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)

.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend \
        build fixtures test test-backend test-frontend check-catalog check-session \
        preview preview-happy \
        docker-build docker-run deploy clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install both toolchains

install-backend: ## Install Python dependencies
	$(PY) -m pip install -r backend/requirements-dev.txt

install-frontend: ## Install Node dependencies
	cd frontend && npm install

dev: ## Run backend (:8080) and Vite (:5173) together
	@echo "Backend on :8080, frontend on http://localhost:5173"
	@trap 'kill 0' EXIT; $(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend: ## Run the API with reload
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8080

dev-frontend: ## Run the Vite dev server (proxies /api and /ws to :8080)
	cd frontend && npm run dev

build: ## Build the SPA into backend/static
	cd frontend && npm run build

fixtures: ## Recapture the A2UI fixtures that drive the offline preview
	$(PY) backend/scripts/generate_fixtures.py

preview-happy: ## Click through the favourable demo offline (see docs/demo-script.md)
	@echo "Capturing the happy-path run — remember: make fixtures to restore."
	$(PY) backend/scripts/generate_fixtures.py --happy
	$(MAKE) build
	@echo "Serving http://localhost:8080/preview.html"
	cd backend && $(PY) -m uvicorn app.main:app --port 8080

preview: build ## Open the offline catalog preview
	@echo "Serving http://localhost:8080/preview.html"
	cd backend && $(PY) -m uvicorn app.main:app --port 8080

test: test-backend test-frontend check-catalog check-session ## Run everything

test-backend: ## Backend unit tests
	cd backend && $(PY) -m pytest -q

test-frontend: ## TypeScript typecheck and formatting
	cd frontend && npm run typecheck && npm run format:check

check-catalog: build ## Render every surface in a browser and check for gaps
	cd frontend && npm run check:catalog

check-session: build ## Drive the shell through restart, in both languages
	cd frontend && CHECK_LOCALE=de npm run check:session
	cd frontend && CHECK_LOCALE=en npm run check:session

docker-build: ## Build the container image
	docker build -t $(SERVICE):local .

docker-run: docker-build ## Run the image locally on :8080
	docker run --rm -p 8080:8080 \
		-e GOOGLE_CLOUD_PROJECT=$(PROJECT) \
		-e GOOGLE_CLOUD_LOCATION=$(REGION) \
		-v $$HOME/.config/gcloud:/home/advisory/.config/gcloud:ro \
		$(SERVICE):local

deploy: ## Build and deploy to Cloud Run
	./deploy/deploy.sh

clean: ## Remove build output and caches
	rm -rf backend/static frontend/dist frontend/node_modules
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	find . -name .pytest_cache -type d -prune -exec rm -rf {} +
