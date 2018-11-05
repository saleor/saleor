# A quick and conveniant way to use this Makefile is by creating a
# make shell alias like the following:
#
# alias saleor='make -f Makefile.dev.example'
#
# then use it as you would make:
#
# saleor <target>

# --build-arg=SKIP_LOCK=$(SKIP_LOCK) \ can be added to the
# image-build target below to build with latest Pipfile.
# SKIP_LOCK=--skip-lock
HOST_UID:=$(shell id -u)
HOST_GID:=$(shell id -g)
HOST_UID?=1000
HOST_GID?=1000
COMPOSE_DEV=docker-compose -f docker-compose.dev.yml
EXEC_WEB=exec web gosu $(HOST_UID)

define BUILD_STATIC_CMD
'npm run build-assets --production &&\
 npm run build-emails --production'
endef

define INIT_EXAMPLE_CMD
'python3 manage.py migrate &&\
 python3 manage.py collectstatic --no-input &&\
 python3 manage.py populatedb --createsuperuser'
endef

define NPM_INSTALL_CMD
'npm install'
endef

default:

build-image:
	$(COMPOSE_DEV) build \
	--build-arg=HOST_UID=$(HOST_UID) \
	--build-arg=HOST_GID=$(HOST_GID)

up:
	$(COMPOSE_DEV) up -d

down:
	$(COMPOSE_DEV) down

start:
	$(COMPOSE_DEV) start

stop:
	$(COMPOSE_DEV) stop

npm-install:
	$(COMPOSE_DEV) $(EXEC_WEB) sh -c $(NPM_INSTALL_CMD)

build-static:
	$(COMPOSE_DEV) $(EXEC_WEB) sh -c $(BUILD_STATIC_CMD)

init-example:
	$(COMPOSE_DEV) $(EXEC_WEB) sh -c $(INIT_EXAMPLE_CMD)

connect-tty-user:
	$(COMPOSE_DEV) $(EXEC_WEB) bash

connect-tty-root:
	$(COMPOSE_DEV) exec web bash
