# Titan

## How to Setup
- Install docker
- Build the image `docker build -t titan .`
- Run `docker run -p 8080:8080 titan`

## Setup Enviroment Variables
- `export DATABASE_URL=postgres://postgres:password@localhost:5432/titan`
- `export SECRET_KEY=changeme`
- `export BUCKET_NAME=mercuriemartstorage`
- `export PAYSTACK_SECRET_KEY=****************`
- `export PAYSTACK_PUBLIC_KEY=****************`
- `export STORE_CATEGORY=groceries`

### Deployed Version: https://demo.mercuriemart.com