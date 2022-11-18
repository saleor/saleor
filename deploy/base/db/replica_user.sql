-- Script being executed on DB init, creates read only user
-- for replicas purposes.
CREATE USER saleor_read_only WITH PASSWORD 'saleor';
GRANT CONNECT ON DATABASE saleor TO saleor_read_only;
GRANT USAGE ON SCHEMA public TO saleor_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO saleor_read_only;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO saleor_read_only;
