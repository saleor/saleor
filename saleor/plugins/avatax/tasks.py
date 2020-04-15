from ...celeryconf import app
from . import api_post_request


@app.task
def api_post_request_task(transaction_url, data, config):
    api_post_request(transaction_url, data, config)
