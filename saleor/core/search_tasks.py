from celery.utils.log import get_task_logger

from ..account.models import User
from ..account.search import prepare_user_search_document_value
from ..celeryconf import app

task_logger = get_task_logger(__name__)

BATCH_SIZE = 10000


@app.task
def set_user_search_document_values(total_count, updated_count):
    qs = User.objects.filter(search_document="").prefetch_related("addresses")[
        :BATCH_SIZE
    ]
    if not qs:
        task_logger.info("Setting user search document values finished.")
        return
    users = []
    for user in qs:
        user.search_document = prepare_user_search_document_value(user)
        users.append(user)
    User.objects.bulk_update(users, ["search_document"])

    updated_count += BATCH_SIZE
    updated_count = min(total_count, updated_count)

    progress = round((updated_count / total_count) * 100, 2)

    task_logger.info(
        f"Updated {updated_count} from {total_count} users - {progress}% done."
    )

    return set_user_search_document_values.delay(total_count, updated_count)
