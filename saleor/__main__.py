import uvicorn

config = uvicorn.Config(
    "saleor.asgi:application", port=8000, reload=True, lifespan="off"
)
server = uvicorn.Server(config)
server.run()
