# Aspire Python AppHost
# For more information, see: https://aspire.dev

from pathlib import Path

from aspire_app import create_builder


with create_builder() as builder:
    repo_root = str(Path(__file__).resolve().parent)
    saleor_image = "saleor-devcontainer:local"

    postgres_user = builder.add_parameter_with_value(
        "postgres-user",
        "saleor",
        publish_value_as_default=True,
    )
    postgres_database = builder.add_parameter_with_value(
        "postgres-database",
        "saleor",
        publish_value_as_default=True,
    )
    postgres_password = builder.add_parameter_with_generated_value(
        "postgres-password",
        {
            "MinLength": 20,
            "Lower": True,
            "Upper": True,
            "Numeric": True,
            "MinLower": 1,
            "MinUpper": 1,
            "MinNumeric": 1,
        },
        secret=True,
        persist=True,
    )
    default_from_email = builder.add_parameter_with_value(
        "default-from-email",
        "noreply@example.com",
        publish_value_as_default=True,
    )
    secret_key = builder.add_parameter_with_generated_value(
        "saleor-secret-key",
        {
            "MinLength": 50,
            "Lower": True,
            "Upper": True,
            "Numeric": True,
            "Special": True,
            "MinLower": 1,
            "MinUpper": 1,
            "MinNumeric": 1,
            "MinSpecial": 1,
        },
        secret=True,
        persist=True,
    )
    allowed_hosts = builder.add_parameter_with_value(
        "allowed-hosts",
        "localhost,127.0.0.1,host.docker.internal,host.containers.internal",
        publish_value_as_default=True,
    )
    allow_loopback_ips = builder.add_parameter_with_value(
        "allow-loopback-ips",
        "True",
        publish_value_as_default=True,
    )

    db = builder.add_container("db", "postgres")
    db.with_image_tag("15-alpine")
    db.with_env("POSTGRES_USER", postgres_user)
    db.with_env("POSTGRES_PASSWORD", postgres_password)
    db.with_env("POSTGRES_DB", postgres_database)
    db.with_endpoint(name="tcp", scheme="tcp", port=5432, target_port=5432)
    db.with_volume("/var/lib/postgresql/data", name="saleor-db")

    cache = builder.add_container("cache", "valkey/valkey")
    cache.with_image_tag("8.1-alpine")
    cache.with_endpoint(name="tcp", scheme="tcp", port=6379, target_port=6379)
    cache.with_volume("/data", name="saleor-cache")

    mailpit = builder.add_container("mailpit", "axllent/mailpit")
    mailpit.with_endpoint(name="smtp", scheme="tcp", port=1025, target_port=1025)
    mailpit.with_http_endpoint(name="http", port=8025, target_port=8025)

    dashboard = builder.add_container("dashboard", "ghcr.io/saleor/saleor-dashboard")
    dashboard.with_image_tag("3.22")
    dashboard.with_http_endpoint(name="http", port=9000, target_port=80)

    saleor_image_build = builder.add_executable(
        "saleor-image-build",
        "docker",
        repo_root,
        ["build", "-f", ".devcontainer/Dockerfile", "-t", saleor_image, "."],
    )

    db_endpoint = db.get_endpoint("tcp")
    cache_endpoint = cache.get_endpoint("tcp")
    mailpit_smtp_endpoint = mailpit.get_endpoint("smtp")
    dashboard_http_endpoint = dashboard.get_endpoint("http")

    def add_saleor_service(name: str, command: str):
        wrapped_command = "\n".join(
            [
                'export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${SALEOR_DB_ENDPOINT#tcp://}/${POSTGRES_DATABASE}"',
                'export CACHE_URL="redis://${SALEOR_CACHE_ENDPOINT#tcp://}/0"',
                'export CELERY_BROKER_URL="redis://${SALEOR_CACHE_ENDPOINT#tcp://}/1"',
                'export EMAIL_URL="smtp://${SALEOR_SMTP_ENDPOINT#tcp://}"',
                'export DASHBOARD_URL="${SALEOR_DASHBOARD_ENDPOINT}"',
                f"exec {command}",
            ]
        )

        resource = builder.add_container(name, "saleor-devcontainer")
        resource.with_image_tag("local")
        resource.with_bind_mount(repo_root, "/app")
        resource.with_container_runtime_args(["-w", "/app"])
        resource.with_entrypoint("bash")
        resource.with_args(["-lc", wrapped_command])
        resource.with_env("POSTGRES_USER", postgres_user)
        resource.with_env("POSTGRES_PASSWORD", postgres_password)
        resource.with_env("POSTGRES_DATABASE", postgres_database)
        resource.with_env("SALEOR_DB_ENDPOINT", db_endpoint)
        resource.with_env("SALEOR_CACHE_ENDPOINT", cache_endpoint)
        resource.with_env("SALEOR_SMTP_ENDPOINT", mailpit_smtp_endpoint)
        resource.with_env("SALEOR_DASHBOARD_ENDPOINT", dashboard_http_endpoint)
        resource.with_env("DEFAULT_FROM_EMAIL", default_from_email)
        resource.with_env("SECRET_KEY", secret_key)
        resource.with_env("ALLOWED_HOSTS", allowed_hosts)
        resource.with_env("HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS", allow_loopback_ips)
        resource.with_otlp_exporter()
        resource.wait_for_completion(saleor_image_build)
        resource.wait_for(db)
        resource.wait_for(cache)
        resource.wait_for(mailpit)
        return resource

    migrate = add_saleor_service("saleor-migrate", "uv run python manage.py migrate")

    api = add_saleor_service(
        "saleor-api",
        "uv run uvicorn saleor.asgi:application --reload --host 0.0.0.0 --port 8000",
    )
    api.wait_for_completion(migrate)
    api.with_http_endpoint(name="http", port=8000, target_port=8000)
    api.with_http_health_check(path="/health/", endpoint_name="http")

    worker = add_saleor_service(
        "saleor-worker",
        "uv run celery --app saleor.celeryconf:app worker -E",
    )
    worker.wait_for_completion(migrate)

    scheduler = add_saleor_service(
        "saleor-scheduler",
        "uv run celery --app saleor.celeryconf:app beat --scheduler saleor.schedulers.schedulers.DatabaseScheduler",
    )
    scheduler.wait_for_completion(migrate)

    builder.run()
