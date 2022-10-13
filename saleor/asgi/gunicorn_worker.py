from uvicorn.workers import UvicornWorker as BaseUvicornWorker


class UvicornWorker(BaseUvicornWorker):
    # Override default config args, that cannot be passed as gunicorn parameters,
    # to disable lifespan, not supported by django
    CONFIG_KWARGS = {"loop": "uvloop", "http": "httptools", "lifespan": "off"}
