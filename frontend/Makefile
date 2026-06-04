# EventHub frontend task runner (Linux/macOS).
# 1:1 mirror of tasks.ps1 (Windows). Keep both in sync.

.PHONY: help install dev build lint fmt typecheck gen-api docker-build up down

help:
	@echo "Targets: install dev build lint fmt typecheck gen-api docker-build up down"

install:
	npm install

dev:
	npm run dev

build:
	npm run build

lint:
	npm run lint

fmt:
	npm run fmt

typecheck:
	npm run typecheck

# Regenerate lib/api/schema.d.ts from the live API's /openapi.json (API must be up).
gen-api:
	npm run gen-api

docker-build:
	docker build -t eventhub-frontend .

# Build + run the frontend container in the background (isolated, mock data).
up:
	docker compose up --build -d

down:
	docker compose down
