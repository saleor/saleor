from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.db.models.query import QuerySet


class SubtypedQuerySet(QuerySet):

    def find_subclasses(self, root):
        for a in dir(root):
            try:
                attr = getattr(root, a)
            except AttributeError:
                continue
            if isinstance(attr, SingleRelatedObjectDescriptor):
                child = attr.related.model
                if (issubclass(child, root) and
                        child is not root):
                    yield a
                    for s in self.find_subclasses(child):
                        yield '%s__%s' % (a, s)

    def subcast(self, obj):
        subtype = obj
        while True:
            root = type(subtype)
            last_root = root
            for a in dir(root):
                try:
                    attr = getattr(root, a)
                except AttributeError:
                    continue
                if isinstance(attr, SingleRelatedObjectDescriptor):
                    child = attr.related.model
                    if (issubclass(child, root) and
                            child is not root):
                        try:
                            next_type = getattr(subtype, a)
                        except models.ObjectDoesNotExist:
                            pass
                        else:
                            subtype = next_type
                            break
            if root == last_root:
                break
        return subtype

    def iterator(self, subclass=True):
        subclasses = list(self.find_subclasses(self.model))
        if subclasses and subclass:
            # https://code.djangoproject.com/ticket/16572
            related = self.select_related(*subclasses)
            for obj in related.iterator(subclass=False):
                yield obj
        else:
            objs = super(SubtypedQuerySet, self).iterator()
            for obj in objs:
                yield self.subcast(obj)


class SubtypedManager(models.Manager):

    use_for_related_fields = True

    def get_query_set(self):
        return SubtypedQuerySet(self.model)


class Subtyped(models.Model):

    objects = SubtypedManager()

    class Meta:
        abstract = True
