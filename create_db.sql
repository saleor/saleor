CREATE ROLE saleor WITH PASSWORD 'saleor' SUPERUSER LOGIN CREATEDB;
CREATE DATABASE saleor  WITH OWNER = saleor  ENCODING = 'UTF8' ;

\c saleor;

CREATE SCHEMA saleor AUTHORIZATION saleor;

ALTER USER saleor SET search_path TO saleor;

ALTER DATABASE saleor SET timezone TO 'UTC';