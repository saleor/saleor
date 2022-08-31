class PrimaryReplicaRouter:
    def allow_relation(self, obj1, obj2, **hints):
        """All relations are allowed as we don't have pool separation."""
        return True
