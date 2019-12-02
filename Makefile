APPVERSION=0.1
APPMAIL="soporte@zentek.com.mx"
NOCLR=\x1b[0m
OKCLR=\x1b[32;01m
ERRCLR=\x1b[31;01m
WARNCLR=\x1b[33;01m
EXECUTABLES=docker pip python3 screen npm yarn
include .env
export $(shell sed 's/=.*//' .env)

define usage =
Build automation tool for saleor, v${APPVERSION}"

Usage:
  make [task]
endef

## Built in tasks ##

#: env - Shows current working environment
env:
	@echo -e "\n\tProfile [${OKCLR}${DJANGO_SETTINGS_MODULE}${NOCLR}]\n"

#: help - Show Test info
help: env
	$(info $(usage))
	@echo -e "\n  Available targets:"
	@egrep -o "^#: (.+)" [Mm]akefile  | sed 's/#: /    /'
	@echo "  Report errors to ${APPMAIL}"

#: check - Check that system requirements are met
check:
	$(info Required programs:)
	$(foreach bin,$(EXECUTABLES),\
	    $(if $(shell command -v $(bin) 2> /dev/null),$(info Found `$(bin)`),$(error Please install `$(bin)`)))
	@make help

# clean-build - Remove build and python files
clean-build:
	@rm -fr lib/
	@rm -fr build/
	@rm -fr dist/
	@rm -fr .tox/
	@rm -fr *.egg-info

# clean-pyc - Remove build and python files
clean-pyc:
	@find ${PROJECT} -name '*.pyc' -exec rm -f {} +
	@find ${PROJECT} -name '*.pyo' -exec rm -f {} +
	@find ${PROJECT} -name '*~' -exec rm -f {} +

# clean-migrations - Remove migrations files
clean-migrations:
	@find ${PROJECT} -path "*/migrations/*.py" -not -name "__init__.py" -delete
	@find ${PROJECT} -name __pycache__ -delete
	@rm -fr media/*

# clean-containers - Remove docker files
clean-containers:
	@docker system prune --volumes

#: clean - Remove build and python files
clean: clean-pyc clean-migrations

#: clean-all - Full clean
clean-all: clean-build clean-pyc clean-migrations clean-containers

#: test - Run test suites.
test:
	py.test

# test-version - Run test from different version managed in tox
test-versions:
	tox

#: coverage - Coverage
coverage:
	coverage erase
	coverage run django-admin test
	coverage html

#: build-docs - Build docs
build-docs:
	sphinx-build -b html docs/ docs/_build/

#: dependencies - Install dependencies
dependencies: env
	pip install -r requirements.txt
	yarn install

# postgres - Start postgres container
postgres: env
	@if [[ ! $$(docker ps -a | grep "${SLUG}-postgres") ]]; then \
		docker run -d --rm --name ${SLUG}-postgres -p ${POSTGRES_PORT}:${POSTGRES_PORT} -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} postgres:9.6-alpine; \
	else \
		echo "[${SLUG}-postgres] There is an existing postgres container name, I will use"; \
	fi

# redis - Start redis container
redis: env
	@if [[ ! $$(docker ps -a | grep "${SLUG}-redis") ]]; then \
		docker run -d --rm --name ${SLUG}-redis -p 6379:6379 redis:5-alpine; \
	else \
		echo "[${SLUG}-redis] There is an existing redis container name, I will use"; \
	fi

#: backend-start - Start backend services
backend-start: postgres redis
	@sleep 2
	@echo "Backend services started..."

#: backend-stop - Start backend services
backend-stop:
	@if [[ $$(docker ps -a | grep "${SLUG}-redis") ]]; then \
		docker stop ${SLUG}-redis; \
	fi; \
	if [[ $$(docker ps -a | grep "${SLUG}-postgres") ]]; then \
		docker stop ${SLUG}-postgres; \
	fi;
	@echo "Backend services stopped..."

#: migrations - Initializes and apply changes to DB
migrations: env clean backend-start
	@python manage.py makemigrations
	@python manage.py migrate

#: fixtures - Load fixtures
fixtures: env
	@python manage.py loaddata fixtures/*.yaml
ifneq ("$(wildcard $(fixtures/*.yaml))","")
	@echo "TIENE FIXTURES"
endif

#: taskqueue-start - Initializes task queue in background
taskqueue-start: env
	@if [[ ! $$(screen -ls | grep -q "worker") ]]; then \
		screen -S worker -dm celery -A ${PROJECT} worker -l info; \
	else \
		echo "There is an existing screen session: worker"; \
	fi
	@if [[ ! $$(screen -ls | grep -q "beat") ]]; then \
		screen -S beat -dm celery -A ${PROJECT} beat -l info -S django; \
	else \
		echo "There is an existing screen session: beat"; \
	fi
	@screen -ls
	@echo -e "\nTo access screen session use the following command:\n\tscreen -x <screen session name>"

taskqueue-stop:
	@pkill screen

#: frontend - Initializes frontend
build-frontend: env
	@npm run build-assets
	@npm run build-emails

#: notebook - Runs notebook
notebook: env
	@jupyter notebook --ip=0.0.0.0 --no-browser --notebook-dir ./notebook

# shell - Access django admin shell
shell:
	@python manage.py shell

# dbshell - Access database shell
dbshell:
	@python manage.py dbshell

# run-dev - Run development mode
run-dev: build-frontend
	@python manage.py runserver

# run-wsgi - Run development mode
run-prod: build-frontend
	@gunicorn --log-level debug ${PROJECT}.wsgi:application

#: run - Run
run: run-dev

#: stop - Stop
stop: backend-stop # taskqueue-stop

#: deploy - Deploy
deploy: env backend-start migrations fixtures run

# build - Push to upload
build:
	docker login
	docker build -t ${UREPO}/${PROJECT} .

# push - Push to upload
push: build
	docker push ${UREPO}/${PROJECT}

#: release - Build and push
release: build push

# compose - Run with docker compose
compose: build
	docker-compose up

.PHONY: clean-pyc clean-build docs clean
.DEFAULT_GOAL := check
