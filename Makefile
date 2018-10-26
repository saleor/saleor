HOST_UID=1000
HOST_GID=100
COMPOSE_DEV=docker-compose -f docker-compose-dev.yml
EXEC_WEB=exec web gosu saleor

define BUILD_STATIC_CMD
'npm run build-assets --production &&\
 npm run build-emails --production'
endef

define INIT_EXAMPLE_CMD
'python3 manage.py migrate &&\
 python3 manage.py collectstatic --no-input &&\
 python3 manage.py populatedb --createsuperuser'
endef

default:

# export BUILD_STATIC_CMD
# def-echo:
# 		@echo "$$BUILD_STATIC_CMD"

dev-build-image:
		$(COMPOSE_DEV) build \
		--build-arg=HOST_UID=$(HOST_UID) \
		--build-arg=HOST_GID=$(HOST_GID)

dev-up:
		$(COMPOSE_DEV) up -d

dev-down:
		$(COMPOSE_DEV) down

dev-start:
		$(COMPOSE_DEV) start

dev-stop:
		$(COMPOSE_DEV) stop

dev-build-static:
		$(COMPOSE_DEV) $(EXEC_WEB) sh -c $(BUILD_STATIC_CMD)

dev-init-example:
		$(COMPOSE_DEV) $(EXEC_WEB) sh -c $(INIT_EXAMPLE_CMD)

dev-connect-tty:
		$(COMPOSE_DEV) $(EXEC_WEB) bash
