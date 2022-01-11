import requests
from celery.utils.log import get_task_logger

from saleor.celeryconf import app
from saleor.plugins.manager import get_plugins_manager
from saleor.plugins.oto.constants import PLUGIN_ID

task_logger = get_task_logger(__name__)


@app.task
def update_oto_access_token_task():
    manager = get_plugins_manager()
    oto_plugin = manager.get_plugin(plugin_id=PLUGIN_ID)
    if oto_plugin.active or not oto_plugin.active:
        task_logger.info("Updating OTO access token")
        # Send refresh token request to OTO
        response = requests.post(
            url="https://api.tryoto.com/rest/v2/refreshToken",
            json={"refresh_token": oto_plugin.config.get("REFRESH_TOKEN")},
        )
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            cleaned_data = {
                "configuration": [
                    {"name": "ACCESS_TOKEN", "value": access_token},
                ],
            }
            manager.save_plugin_configuration(
                plugin_id=PLUGIN_ID, channel_slug=None, cleaned_data=cleaned_data
            )
        # Update access token in plugin configuration
        task_logger.info("Successfully updated OTO access token")
        return response
