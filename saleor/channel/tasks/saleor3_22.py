from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import Channel


@app.task
@allow_writer()
def set_automatic_completion_delay_task():
    Channel.objects.filter(automatically_complete_fully_paid_checkouts=True).update(
        automatic_completion_delay=0
    )
