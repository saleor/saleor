from enum import Enum


class AccountErrorCode(Enum):
    ACTIVATE_OWN_ACCOUNT = "activate_own_account"
    ACTIVATE_SUPERUSER_ACCOUNT = "activate_superuser_account"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    DEACTIVATE_OWN_ACCOUNT = "deactivate_own_account"
    DEACTIVATE_SUPERUSER_ACCOUNT = "deactivate_superuser_account"
    DELETE_NON_STAFF_USER = "delete_non_staff_user"
    DELETE_OWN_ACCOUNT = "delete_own_account"
    DELETE_STAFF_ACCOUNT = "delete_staff_account"
    DELETE_SUPERUSER_ACCOUNT = "delete_superuser_account"
    GRAPHQL_ERROR = "graphql_error"
    INACTIVE = "inactive"
    INVALID = "invalid"
    INVALID_PASSWORD = "invalid_password"
    LEFT_NOT_MANAGEABLE_PERMISSION = "left_not_manageable_permission"
    INVALID_CREDENTIALS = "invalid_credentials"
    NOT_FOUND = "not_found"
    OUT_OF_SCOPE_USER = "out_of_scope_user"
    OUT_OF_SCOPE_GROUP = "out_of_scope_group"
    OUT_OF_SCOPE_PERMISSION = "out_of_scope_permission"
    PASSWORD_ENTIRELY_NUMERIC = "password_entirely_numeric"
    PASSWORD_TOO_COMMON = "password_too_common"
    PASSWORD_TOO_SHORT = "password_too_short"
    PASSWORD_TOO_SIMILAR = "password_too_similar"
    PASSWORD_RESET_ALREADY_REQUESTED = "password_reset_already_requested"
    REQUIRED = "required"
    UNIQUE = "unique"
    JWT_SIGNATURE_EXPIRED = "signature_has_expired"
    JWT_INVALID_TOKEN = "invalid_token"
    JWT_DECODE_ERROR = "decode_error"
    JWT_MISSING_TOKEN = "missing_token"
    JWT_INVALID_CSRF_TOKEN = "invalid_csrf_token"
    CHANNEL_INACTIVE = "channel_inactive"
    MISSING_CHANNEL_SLUG = "missing_channel_slug"
    ACCOUNT_NOT_CONFIRMED = "account_not_confirmed"
    LOGIN_ATTEMPT_DELAYED = "login_attempt_delayed"
    UNKNOWN_IP_ADDRESS = "unknown_ip_address"


class CustomerBulkUpdateErrorCode(Enum):
    BLANK = "blank"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    REQUIRED = "required"
    UNIQUE = "unique"
    NOT_FOUND = "not_found"
    MAX_LENGTH = "max_length"


class PermissionGroupErrorCode(Enum):
    REQUIRED = "required"
    UNIQUE = "unique"
    ASSIGN_NON_STAFF_MEMBER = "assign_non_staff_member"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    CANNOT_REMOVE_FROM_LAST_GROUP = "cannot_remove_from_last_group"
    LEFT_NOT_MANAGEABLE_PERMISSION = "left_not_manageable_permission"
    OUT_OF_SCOPE_PERMISSION = "out_of_scope_permission"
    OUT_OF_SCOPE_USER = "out_of_scope_user"
    OUT_OF_SCOPE_CHANNEL = "out_of_scope_channel"


class SendConfirmationEmailErrorCode(Enum):
    INVALID = "invalid"
    ACCOUNT_CONFIRMED = "account_confirmed"
    CONFIRMATION_ALREADY_REQUESTED = "confirmation_already_requested"
    MISSING_CHANNEL_SLUG = "missing_channel_slug"


class CustomerGroupErrorCode(Enum):
    UNIQUE = "unique"
