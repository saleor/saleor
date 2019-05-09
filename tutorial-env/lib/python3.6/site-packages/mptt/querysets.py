from django.db import models

from mptt import utils


class TreeQuerySet(models.query.QuerySet):
    def get_descendants(self, *args, **kwargs):
        """
        Alias to `mptt.managers.TreeManager.get_queryset_descendants`.
        """
        return self.model._tree_manager.get_queryset_descendants(self, *args, **kwargs)
    get_descendants.queryset_only = True

    def get_ancestors(self, *args, **kwargs):
        """
        Alias to `mptt.managers.TreeManager.get_queryset_ancestors`.
        """
        return self.model._tree_manager.get_queryset_ancestors(self, *args, **kwargs)
    get_ancestors.queryset_only = True

    def get_cached_trees(self):
        """
        Alias to `mptt.utils.get_cached_trees`.
        """
        return utils.get_cached_trees(self)
