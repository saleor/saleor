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
		web gosu saleor sh -c \
		'npm install && \
        npm run build-assets --producion && \
        npm run build-emails --producion && \
        python3 manage.py migrate && \
		python3 manage.py collectstatic && \
		python3 manage.py populatedb --createsuperuser' \
		-d

up-init-dev:
		docker-compose up -d
		docker-compose exec \
		web gosu saleor sh -c \
		'npm install && \
        npm run build-assets --producion && \
        npm run build-emails --producion && \
        python3 manage.py migrate && \
		python3 manage.py collectstatic && \
		python3 manage.py populatedb --createsuperuser' \
		-d

# end
