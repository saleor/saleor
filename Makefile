.PHONY: runserver migrate populatedb test help build-schema release

help: ## Display this help message
	@echo "Saleor Development Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

runserver: ## Start the development server with auto-reload
	uvicorn saleor.asgi:application --reload

migrate: ## Run database migrations
	python manage.py migrate

populatedb: ## Populate database with example data and create superuser
	python manage.py populatedb --createsuperuser

test: ## Run tests with database reuse
	pytest --reuse-db

build-schema: ## Build GraphQL schema
	npm run build-schema

release: ## Create a new release
	npm run release
