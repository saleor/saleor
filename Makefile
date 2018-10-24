##
# Twincam Web Store
#
# @file
# @version 0.1

default:

build-static:
        docker-compose exec \
        web sh -c \
        'gosu saleor npm run build-assets --production && \
        gosu saleor npm run build-emails --production'

init-dev:
		docker-compose exec \
		web sh -c \
		'gosu saleor python3 manage.py migrate && \
		gosu saleor python3 manage.py collectstatic && \
		gosu saleor python3 manage.py populatedb --createsuperuser' \
		-d

up-init-dev:
		docker-compose up -d
		docker-compose exec \
		web sh -c \
		'gosu saleor python3 manage.py migrate && \
		gosu saleor python3 manage.py collectstatic && \
		gosu saleor python3 manage.py populatedb --createsuperuser' \
		-d

# end
