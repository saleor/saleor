import uvicorn

config = uvicorn.Config(
    "saleor.asgi:application", port=8000, reload=True, lifespan="on"
)
server = uvicorn.Server(config)
server.run()
