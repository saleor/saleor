from django.db.models.lookups import IContains


class PostgresILike(IContains):
    lookup_name = "ilike"

    def as_postgresql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s ILIKE %s" % (lhs, rhs), params
