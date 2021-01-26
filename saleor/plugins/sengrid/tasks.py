from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ...celeryconf import app
from . import SengridConfiguration


@app.task
def send_email_task(configuration: SengridConfiguration, email_event, payload):
    sengrid_client = SendGridAPIClient(configuration.api_key)
