import logging
from haystack import connections

logger = logging.getLogger(__name__)


def update_object(instance, using='default'):
    all_indexes = connections[using].get_unified_index().get_indexes()
    index = all_indexes.get(instance.__class__)
    if index:
        index.update_object(instance)
    else:
        logger.warning('Tried to index object without matching index',
                       extra={'instance': instance, 'all_indexes': all_indexes})
