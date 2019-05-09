from .arguments_of_correct_type import ArgumentsOfCorrectType
from .default_values_of_correct_type import DefaultValuesOfCorrectType
from .fields_on_correct_type import FieldsOnCorrectType
from .fragments_on_composite_types import FragmentsOnCompositeTypes
from .known_argument_names import KnownArgumentNames
from .known_directives import KnownDirectives
from .known_fragment_names import KnownFragmentNames
from .known_type_names import KnownTypeNames
from .lone_anonymous_operation import LoneAnonymousOperation
from .no_fragment_cycles import NoFragmentCycles
from .no_undefined_variables import NoUndefinedVariables
from .no_unused_fragments import NoUnusedFragments
from .no_unused_variables import NoUnusedVariables
from .overlapping_fields_can_be_merged import OverlappingFieldsCanBeMerged
from .possible_fragment_spreads import PossibleFragmentSpreads
from .provided_non_null_arguments import ProvidedNonNullArguments
from .scalar_leafs import ScalarLeafs
from .unique_argument_names import UniqueArgumentNames
from .unique_fragment_names import UniqueFragmentNames
from .unique_input_field_names import UniqueInputFieldNames
from .unique_operation_names import UniqueOperationNames
from .unique_variable_names import UniqueVariableNames
from .variables_are_input_types import VariablesAreInputTypes
from .variables_in_allowed_position import VariablesInAllowedPosition

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import List, Type
    from .base import ValidationRule


specified_rules = [
    UniqueOperationNames,
    LoneAnonymousOperation,
    KnownTypeNames,
    FragmentsOnCompositeTypes,
    VariablesAreInputTypes,
    ScalarLeafs,
    FieldsOnCorrectType,
    UniqueFragmentNames,
    KnownFragmentNames,
    NoUnusedFragments,
    PossibleFragmentSpreads,
    NoFragmentCycles,
    NoUndefinedVariables,
    NoUnusedVariables,
    KnownDirectives,
    KnownArgumentNames,
    UniqueArgumentNames,
    ArgumentsOfCorrectType,
    ProvidedNonNullArguments,
    DefaultValuesOfCorrectType,
    VariablesInAllowedPosition,
    OverlappingFieldsCanBeMerged,
    UniqueInputFieldNames,
    UniqueVariableNames,
]  # type: List[Type[ValidationRule]]

__all__ = [
    "ArgumentsOfCorrectType",
    "DefaultValuesOfCorrectType",
    "FieldsOnCorrectType",
    "FragmentsOnCompositeTypes",
    "KnownArgumentNames",
    "KnownDirectives",
    "KnownFragmentNames",
    "KnownTypeNames",
    "LoneAnonymousOperation",
    "NoFragmentCycles",
    "UniqueVariableNames",
    "NoUndefinedVariables",
    "NoUnusedFragments",
    "NoUnusedVariables",
    "OverlappingFieldsCanBeMerged",
    "PossibleFragmentSpreads",
    "ProvidedNonNullArguments",
    "ScalarLeafs",
    "UniqueArgumentNames",
    "UniqueFragmentNames",
    "UniqueInputFieldNames",
    "UniqueOperationNames",
    "VariablesAreInputTypes",
    "VariablesInAllowedPosition",
    "specified_rules",
]
