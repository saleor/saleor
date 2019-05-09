from ...error import GraphQLError
from .base import ValidationRule


class KnownFragmentNames(ValidationRule):
    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        fragment_name = node.name.value
        fragment = self.context.get_fragment(fragment_name)

        if not fragment:
            self.context.report_error(
                GraphQLError(self.unknown_fragment_message(fragment_name), [node.name])
            )

    @staticmethod
    def unknown_fragment_message(fragment_name):
        return 'Unknown fragment "{}".'.format(fragment_name)
