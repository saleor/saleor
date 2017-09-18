OYE Records Backend
======

Installation
------------

Prerequisites:
* You need to have `docker` and `docker-compose` installed on 
your host machine
* The configuration is set to connect to a database that runs outside the 
docker ecosystem. Please make sure, you have a running database with a 
dedicated user with granted r/w access. Please refer to the `.env-template` file 
to find out more about the configuration documentation.
* The `docker-compose.yml` is configured to run on `network_mode host`, so make
sure you have a well configured firewall. Otherwise your app ports could be 
exposed.


```
# Clone git repository
git clone https://github.com/tillkolter/saleor

# Configure environment file
cp .env-template .env
# ... edit .env file and fill the unspecified variable
vim .env 

# Habitus 
./install-habitus.sh
./run-habitus.sh [YOUR DOCKER HOST IP]
```

Usage
-----

```
docker-compose up -d 
```
