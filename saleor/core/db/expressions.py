from django.db.models import Case, F, JSONField, Value, When
from django.db.models.expressions import Expression


class PostgresJsonConcatenate(Expression):
    """Implementation of PostgreSQL concatenation for JSON fields.

    Inserts or updates specific keys provided in the database for `jsonb` field type.
    If a specified keys exists, they will be updated, otherwise they will be inserted.
    Accepts only expressions representing the `django.db.models.JSONField`.

    None values will be transformed to empty `JSON`.
    Similarily if updated jsonb in databse is NULL it will be treated as
    empty `JSON`.

    Examples
        Updating exising json field with new_dict.

        Model.objects.update(
            json_field=PostgresJsonConcatenate(
                F('json_field'), Value(new_dict, output_field=JSONField())
            )
        )

    """

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
            raise TypeError("%r is not a JSONField", arg)

    def resolve_expression(
        self, query=None, allow_joins=False, reuse=None, summarize=False, for_save=True
    ):
        c = self.copy()
        c.left = self.__handle_null_value(self.left)
        c.right = self.__handle_null_value(self.right)
        c.is_summary = summarize
        c.left = c.left.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        c.right = c.right.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        return c

    def __add_case_when(self, arg):
        is_null = {f"{arg.name}__isnull": True}
        c = Case(When(**is_null, then=Value({}, output_field=JSONField())), default=arg)
        return c

    def __handle_null_value(self, arg):
        if isinstance(arg, F):
            return self.__add_case_when(arg)
        if isinstance(arg, Value):
            c = arg.copy()
            if arg.value is None:
                c.value = {}
            return c
        return arg

    def as_postgresql(self, compiler, __connection, template=None):
        sql_params = []
        sql_left, param = compiler.compile(self.left)
        sql_params.extend(param)
        sql_right, param = compiler.compile(self.right)
        sql_params.extend(param)

        template = template or self.template
        data = {"left": sql_left, "right": sql_right}
        return template % data, sql_params
