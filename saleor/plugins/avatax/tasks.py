from ...celeryconf import app
from . import AvataxConfiguration, api_post_request


@app.task
def api_post_request_task(transaction_url, data, config):
    config = AvataxConfiguration(**config)
    api_post_request(transaction_url, data, config)
