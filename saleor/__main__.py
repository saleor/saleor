import uvicorn


config = uvicorn.Config(
    "saleor.asgi:application",
    port=8000,
    lifespan="off",
    workers=4,
    log_level="debug",
    loop="uvloop",
)
server = uvicorn.Server(config)
server.run()
