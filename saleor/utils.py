# coding: utf-8

from django import forms


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr)
        indent = max(0, level - 1) * u'│'
        if obj.parent:
            last = ((obj.parent.rght - obj.rght == 1)
                    and (obj.rght - obj.lft == 1))
            if last:
                indent += u'└ '
            else:
                indent += u'├ '
        return u'%s%s' % (indent, unicode(obj))
