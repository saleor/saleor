def health_check(application, health_url):
    async def health_check_wrapper(scope, receive, send):
        if scope.get("path") != health_url:
            await application(scope, receive, send)
            return
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send({"type": "http.response.body"})

    return health_check_wrapper
