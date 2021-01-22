from .....celeryconf import app
from . import AvataxExciseConfiguration, api_post_request


@app.task
def api_post_request_task(transaction_url, data, config):
    config = AvataxExciseConfiguration(**config)
    api_post_request(transaction_url, data, config)
