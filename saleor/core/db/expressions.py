from django.db.models import JSONField
from django.db.models.expressions import Expression


class JsonCat(Expression):
    # It's possible to recursevily create that expression to allow to pass
    # more than 2 arguments. If needed it can be extended in future
    template = "%(left)s || %(right)s"
    output_field = JSONField()

    def __init__(self, left_arg, right_arg):
        super().__init__(output_field=self.output_field)
        self.__validate_argument(left_arg)
        self.__validate_argument(right_arg)
        self.left = left_arg
        self.right = right_arg

    def __validate_argument(self, arg):
        if not hasattr(arg, "resolve_expression"):
            # make sure that argument is Expression
            raise TypeError("%r is not an Expression", arg)
        if hasattr(arg, "output_field") and not isinstance(arg.output_field, JSONField):
            # force developer to explicitly set value as JSONField
            # e.g. Value({}, output_field=JSONField())
            raise TypeError("%r is not JSONField", arg)

    def resolve_expression(
        self, query=None, allow_joins=False, reuse=None, summarize=False, for_save=True
    ):
        c = self.copy()
        c.is_summary = summarize
        c.left = self.left.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        c.right = self.right.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        return c

    def as_sql(self, compiler, __connection, template=None):
        sql_params = []
        sql_left, param = compiler.compile(self.left)
        sql_params.extend(param)
        sql_right, param = compiler.compile(self.right)
        sql_params.extend(param)

        template = template or self.template
        data = {"left": sql_left, "right": sql_right}
        return template % data, sql_params
