# DO NOT FORK SALEOR TO EXTEND IT
# Learn more https://docs.saleor.io/docs/3.x/developer/extending/overview#why-not-to-fork

import uvicorn

config = uvicorn.Config(
    "saleor.asgi:application", port=8000, reload=True, lifespan="off"
)
server = uvicorn.Server(config)
server.run()
