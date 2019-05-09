from django.db.models.signals import ModelSignal

# Behaves like Djangos normal pre-/post_save signals signals with the
# added arguments ``target`` and ``position`` that matches those of
# ``move_to``.
# If the signal is called from ``save`` it'll not be pass position.

node_moved = ModelSignal(providing_args=[
    'instance',
    'target',
    'position'
])
