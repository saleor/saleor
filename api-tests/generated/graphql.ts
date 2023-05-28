/* eslint-disable */
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string | number; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /**
   * The `Date` scalar type represents a Date
   * value as specified by
   * [iso8601](https://en.wikipedia.org/wiki/ISO_8601).
   */
  Date: { input: any; output: any; }
  /**
   * The `DateTime` scalar type represents a DateTime
   * value as specified by
   * [iso8601](https://en.wikipedia.org/wiki/ISO_8601).
   */
  DateTime: { input: any; output: any; }
  /** The `Day` scalar type represents number of days by integer value. */
  Day: { input: any; output: any; }
  /**
   * Custom Decimal implementation.
   *
   * Returns Decimal as a float in the API,
   * parses float to the Decimal on the way back.
   */
  Decimal: { input: any; output: any; }
  /**
   * The `GenericScalar` scalar type represents a generic
   * GraphQL scalar value that could be:
   * String, Boolean, Int, Float, List or Object.
   */
  GenericScalar: { input: any; output: any; }
  JSON: { input: any; output: any; }
  JSONString: { input: any; output: any; }
  /**
   * Metadata is a map of key-value pairs, both keys and values are `String`.
   *
   * Example:
   * ```
   * {
   *     "key1": "value1",
   *     "key2": "value2"
   * }
   * ```
   */
  Metadata: { input: any; output: any; }
  /** The `Minute` scalar type represents number of minutes by integer value. */
  Minute: { input: any; output: any; }
  /**
   * Nonnegative Decimal scalar implementation.
   *
   * Should be used in places where value must be nonnegative (0 or greater).
   */
  PositiveDecimal: { input: any; output: any; }
  UUID: { input: any; output: any; }
  /** Variables of this type must be set to null in mutations. They will be replaced with a filename from a following multipart part containing a binary file. See: https://github.com/jaydenseric/graphql-multipart-request-spec. */
  Upload: { input: any; output: any; }
  WeightScalar: { input: any; output: any; }
  /** _Any value scalar as defined by Federation spec. */
  _Any: { input: any; output: any; }
};

/**
 * Create a new address for the customer.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type AccountAddressCreate = {
  __typename?: 'AccountAddressCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user instance for which the address was created. */
  user?: Maybe<User>;
};

/** Delete an address of the logged-in user. Requires one of the following permissions: MANAGE_USERS, IS_OWNER. */
export type AccountAddressDelete = {
  __typename?: 'AccountAddressDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user instance for which the address was deleted. */
  user?: Maybe<User>;
};

/** Updates an address of the logged-in user. Requires one of the following permissions: MANAGE_USERS, IS_OWNER. */
export type AccountAddressUpdate = {
  __typename?: 'AccountAddressUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user object for which the address was edited. */
  user?: Maybe<User>;
};

/**
 * Remove user account.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type AccountDelete = {
  __typename?: 'AccountDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  user?: Maybe<User>;
};

/** Represents errors in account mutations. */
export type AccountError = {
  __typename?: 'AccountError';
  /** A type of address that causes the error. */
  addressType?: Maybe<AddressTypeEnum>;
  /** The error code. */
  code: AccountErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum AccountErrorCode {
  AccountNotConfirmed = 'ACCOUNT_NOT_CONFIRMED',
  ActivateOwnAccount = 'ACTIVATE_OWN_ACCOUNT',
  ActivateSuperuserAccount = 'ACTIVATE_SUPERUSER_ACCOUNT',
  ChannelInactive = 'CHANNEL_INACTIVE',
  DeactivateOwnAccount = 'DEACTIVATE_OWN_ACCOUNT',
  DeactivateSuperuserAccount = 'DEACTIVATE_SUPERUSER_ACCOUNT',
  DeleteNonStaffUser = 'DELETE_NON_STAFF_USER',
  DeleteOwnAccount = 'DELETE_OWN_ACCOUNT',
  DeleteStaffAccount = 'DELETE_STAFF_ACCOUNT',
  DeleteSuperuserAccount = 'DELETE_SUPERUSER_ACCOUNT',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Inactive = 'INACTIVE',
  Invalid = 'INVALID',
  InvalidCredentials = 'INVALID_CREDENTIALS',
  InvalidPassword = 'INVALID_PASSWORD',
  JwtDecodeError = 'JWT_DECODE_ERROR',
  JwtInvalidCsrfToken = 'JWT_INVALID_CSRF_TOKEN',
  JwtInvalidToken = 'JWT_INVALID_TOKEN',
  JwtMissingToken = 'JWT_MISSING_TOKEN',
  JwtSignatureExpired = 'JWT_SIGNATURE_EXPIRED',
  LeftNotManageablePermission = 'LEFT_NOT_MANAGEABLE_PERMISSION',
  MissingChannelSlug = 'MISSING_CHANNEL_SLUG',
  NotFound = 'NOT_FOUND',
  OutOfScopeGroup = 'OUT_OF_SCOPE_GROUP',
  OutOfScopePermission = 'OUT_OF_SCOPE_PERMISSION',
  OutOfScopeUser = 'OUT_OF_SCOPE_USER',
  PasswordEntirelyNumeric = 'PASSWORD_ENTIRELY_NUMERIC',
  PasswordResetAlreadyRequested = 'PASSWORD_RESET_ALREADY_REQUESTED',
  PasswordTooCommon = 'PASSWORD_TOO_COMMON',
  PasswordTooShort = 'PASSWORD_TOO_SHORT',
  PasswordTooSimilar = 'PASSWORD_TOO_SIMILAR',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

/** Fields required to update the user. */
export type AccountInput = {
  /** Billing address of the customer. */
  defaultBillingAddress?: InputMaybe<AddressInput>;
  /** Shipping address of the customer. */
  defaultShippingAddress?: InputMaybe<AddressInput>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User language code. */
  languageCode?: InputMaybe<LanguageCodeEnum>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
};

/** Register a new user. */
export type AccountRegister = {
  __typename?: 'AccountRegister';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** Informs whether users need to confirm their email address. */
  requiresConfirmation?: Maybe<Scalars['Boolean']['output']>;
  user?: Maybe<User>;
};

/** Fields required to create a user. */
export type AccountRegisterInput = {
  /** Slug of a channel which will be used to notify users. Optional when only one channel exists. */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** The email address of the user. */
  email: Scalars['String']['input'];
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User language code. */
  languageCode?: InputMaybe<LanguageCodeEnum>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /** User public metadata. */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Password. */
  password: Scalars['String']['input'];
  /** Base of frontend URL that will be needed to create confirmation URL. */
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Sends an email with the account removal link for the logged-in user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type AccountRequestDeletion = {
  __typename?: 'AccountRequestDeletion';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
};

/**
 * Sets a default address for the authenticated user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type AccountSetDefaultAddress = {
  __typename?: 'AccountSetDefaultAddress';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** An updated user instance. */
  user?: Maybe<User>;
};

/**
 * Updates the account of the logged-in user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type AccountUpdate = {
  __typename?: 'AccountUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  user?: Maybe<User>;
};

/** Represents user address data. */
export type Address = Node & ObjectWithMetadata & {
  __typename?: 'Address';
  city: Scalars['String']['output'];
  cityArea: Scalars['String']['output'];
  companyName: Scalars['String']['output'];
  /** Shop's default country. */
  country: CountryDisplay;
  countryArea: Scalars['String']['output'];
  firstName: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** Address is user's default billing address. */
  isDefaultBillingAddress?: Maybe<Scalars['Boolean']['output']>;
  /** Address is user's default shipping address. */
  isDefaultShippingAddress?: Maybe<Scalars['Boolean']['output']>;
  lastName: Scalars['String']['output'];
  /**
   * List of public metadata items. Can be accessed without permissions.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  phone?: Maybe<Scalars['String']['output']>;
  postalCode: Scalars['String']['output'];
  /**
   * List of private metadata items. Requires staff permissions to access.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.10.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  streetAddress1: Scalars['String']['output'];
  streetAddress2: Scalars['String']['output'];
};


/** Represents user address data. */
export type AddressMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents user address data. */
export type AddressMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents user address data. */
export type AddressPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents user address data. */
export type AddressPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Creates user address.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type AddressCreate = {
  __typename?: 'AddressCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user instance for which the address was created. */
  user?: Maybe<User>;
};

/**
 * Event sent when new address is created.
 *
 * Added in Saleor 3.5.
 */
export type AddressCreated = Event & {
  __typename?: 'AddressCreated';
  /** The address the event relates to. */
  address?: Maybe<Address>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes an address.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type AddressDelete = {
  __typename?: 'AddressDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user instance for which the address was deleted. */
  user?: Maybe<User>;
};

/**
 * Event sent when address is deleted.
 *
 * Added in Saleor 3.5.
 */
export type AddressDeleted = Event & {
  __typename?: 'AddressDeleted';
  /** The address the event relates to. */
  address?: Maybe<Address>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type AddressInput = {
  /** City. */
  city?: InputMaybe<Scalars['String']['input']>;
  /** District. */
  cityArea?: InputMaybe<Scalars['String']['input']>;
  /** Company or organization. */
  companyName?: InputMaybe<Scalars['String']['input']>;
  /** Country. */
  country?: InputMaybe<CountryCode>;
  /** State or province. */
  countryArea?: InputMaybe<Scalars['String']['input']>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /** Phone number. */
  phone?: InputMaybe<Scalars['String']['input']>;
  /** Postal code. */
  postalCode?: InputMaybe<Scalars['String']['input']>;
  /** Address. */
  streetAddress1?: InputMaybe<Scalars['String']['input']>;
  /** Address. */
  streetAddress2?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Sets a default address for the given user.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type AddressSetDefault = {
  __typename?: 'AddressSetDefault';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** An updated user instance. */
  user?: Maybe<User>;
};

/** An enumeration. */
export enum AddressTypeEnum {
  Billing = 'BILLING',
  Shipping = 'SHIPPING'
}

/**
 * Updates an address.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type AddressUpdate = {
  __typename?: 'AddressUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  address?: Maybe<Address>;
  errors: Array<AccountError>;
  /** A user object for which the address was edited. */
  user?: Maybe<User>;
};

/**
 * Event sent when address is updated.
 *
 * Added in Saleor 3.5.
 */
export type AddressUpdated = Event & {
  __typename?: 'AddressUpdated';
  /** The address the event relates to. */
  address?: Maybe<Address>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents address validation rules for a country. */
export type AddressValidationData = {
  __typename?: 'AddressValidationData';
  addressFormat: Scalars['String']['output'];
  addressLatinFormat: Scalars['String']['output'];
  allowedFields: Array<Scalars['String']['output']>;
  cityAreaChoices: Array<ChoiceValue>;
  cityAreaType: Scalars['String']['output'];
  cityChoices: Array<ChoiceValue>;
  cityType: Scalars['String']['output'];
  countryAreaChoices: Array<ChoiceValue>;
  countryAreaType: Scalars['String']['output'];
  countryCode: Scalars['String']['output'];
  countryName: Scalars['String']['output'];
  postalCodeExamples: Array<Scalars['String']['output']>;
  postalCodeMatchers: Array<Scalars['String']['output']>;
  postalCodePrefix: Scalars['String']['output'];
  postalCodeType: Scalars['String']['output'];
  requiredFields: Array<Scalars['String']['output']>;
  upperFields: Array<Scalars['String']['output']>;
};

/** Represents allocation. */
export type Allocation = Node & {
  __typename?: 'Allocation';
  id: Scalars['ID']['output'];
  /**
   * Quantity allocated for orders.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  quantity: Scalars['Int']['output'];
  /**
   * The warehouse were items were allocated.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  warehouse: Warehouse;
};

/**
 * Determine the allocation strategy for the channel.
 *
 *     PRIORITIZE_SORTING_ORDER - allocate stocks according to the warehouses' order
 *     within the channel
 *
 *     PRIORITIZE_HIGH_STOCK - allocate stock in a warehouse with the most stock
 *
 */
export enum AllocationStrategyEnum {
  PrioritizeHighStock = 'PRIORITIZE_HIGH_STOCK',
  PrioritizeSortingOrder = 'PRIORITIZE_SORTING_ORDER'
}

/** Represents app data. */
export type App = Node & ObjectWithMetadata & {
  __typename?: 'App';
  /** Description of this app. */
  aboutApp?: Maybe<Scalars['String']['output']>;
  /** JWT token used to authenticate by thridparty app. */
  accessToken?: Maybe<Scalars['String']['output']>;
  /** URL to iframe with the app. */
  appUrl?: Maybe<Scalars['String']['output']>;
  /**
   * The App's author name.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  author?: Maybe<Scalars['String']['output']>;
  /**
   * URL to iframe with the configuration for the app.
   * @deprecated This field will be removed in Saleor 4.0. Use `appUrl` instead.
   */
  configurationUrl?: Maybe<Scalars['String']['output']>;
  /** The date and time when the app was created. */
  created?: Maybe<Scalars['DateTime']['output']>;
  /**
   * Description of the data privacy defined for this app.
   * @deprecated This field will be removed in Saleor 4.0. Use `dataPrivacyUrl` instead.
   */
  dataPrivacy?: Maybe<Scalars['String']['output']>;
  /** URL to details about the privacy policy on the app owner page. */
  dataPrivacyUrl?: Maybe<Scalars['String']['output']>;
  /**
   * App's dashboard extensions.
   *
   * Added in Saleor 3.1.
   */
  extensions: Array<AppExtension>;
  /** Homepage of the app. */
  homepageUrl?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Determine if app will be set active or not. */
  isActive?: Maybe<Scalars['Boolean']['output']>;
  /**
   * URL to manifest used during app's installation.
   *
   * Added in Saleor 3.5.
   */
  manifestUrl?: Maybe<Scalars['String']['output']>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Name of the app. */
  name?: Maybe<Scalars['String']['output']>;
  /** List of the app's permissions. */
  permissions?: Maybe<Array<Permission>>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Support page for the app. */
  supportUrl?: Maybe<Scalars['String']['output']>;
  /**
   * Last 4 characters of the tokens.
   *
   * Requires one of the following permissions: MANAGE_APPS, OWNER.
   */
  tokens?: Maybe<Array<AppToken>>;
  /** Type of the app. */
  type?: Maybe<AppTypeEnum>;
  /** Version number of the app. */
  version?: Maybe<Scalars['String']['output']>;
  /**
   * List of webhooks assigned to this app.
   *
   * Requires one of the following permissions: MANAGE_APPS, OWNER.
   */
  webhooks?: Maybe<Array<Webhook>>;
};


/** Represents app data. */
export type AppMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents app data. */
export type AppMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents app data. */
export type AppPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents app data. */
export type AppPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Activate the app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppActivate = {
  __typename?: 'AppActivate';
  app?: Maybe<App>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
};

export type AppCountableConnection = {
  __typename?: 'AppCountableConnection';
  edges: Array<AppCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type AppCountableEdge = {
  __typename?: 'AppCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: App;
};

/** Creates a new app. Requires the following permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS. */
export type AppCreate = {
  __typename?: 'AppCreate';
  app?: Maybe<App>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  /** The newly created authentication token. */
  authToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AppError>;
};

/**
 * Deactivate the app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppDeactivate = {
  __typename?: 'AppDeactivate';
  app?: Maybe<App>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
};

/**
 * Deletes an app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppDelete = {
  __typename?: 'AppDelete';
  app?: Maybe<App>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
};

/**
 * Delete failed installation.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppDeleteFailedInstallation = {
  __typename?: 'AppDeleteFailedInstallation';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  appInstallation?: Maybe<AppInstallation>;
  errors: Array<AppError>;
};

/**
 * Event sent when app is deleted.
 *
 * Added in Saleor 3.4.
 */
export type AppDeleted = Event & {
  __typename?: 'AppDeleted';
  /** The application the event relates to. */
  app?: Maybe<App>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type AppError = {
  __typename?: 'AppError';
  /** The error code. */
  code: AppErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of permissions which causes the error. */
  permissions?: Maybe<Array<PermissionEnum>>;
};

/** An enumeration. */
export enum AppErrorCode {
  Forbidden = 'FORBIDDEN',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidCustomHeaders = 'INVALID_CUSTOM_HEADERS',
  InvalidManifestFormat = 'INVALID_MANIFEST_FORMAT',
  InvalidPermission = 'INVALID_PERMISSION',
  InvalidStatus = 'INVALID_STATUS',
  InvalidUrlFormat = 'INVALID_URL_FORMAT',
  ManifestUrlCantConnect = 'MANIFEST_URL_CANT_CONNECT',
  NotFound = 'NOT_FOUND',
  OutOfScopeApp = 'OUT_OF_SCOPE_APP',
  OutOfScopePermission = 'OUT_OF_SCOPE_PERMISSION',
  Required = 'REQUIRED',
  Unique = 'UNIQUE',
  UnsupportedSaleorVersion = 'UNSUPPORTED_SALEOR_VERSION'
}

/** Represents app data. */
export type AppExtension = Node & {
  __typename?: 'AppExtension';
  /** JWT token used to authenticate by thridparty app extension. */
  accessToken?: Maybe<Scalars['String']['output']>;
  app: App;
  id: Scalars['ID']['output'];
  /** Label of the extension to show in the dashboard. */
  label: Scalars['String']['output'];
  /** Place where given extension will be mounted. */
  mount: AppExtensionMountEnum;
  /** List of the app extension's permissions. */
  permissions: Array<Permission>;
  /** Type of way how app extension will be opened. */
  target: AppExtensionTargetEnum;
  /** URL of a view where extension's iframe is placed. */
  url: Scalars['String']['output'];
};

export type AppExtensionCountableConnection = {
  __typename?: 'AppExtensionCountableConnection';
  edges: Array<AppExtensionCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type AppExtensionCountableEdge = {
  __typename?: 'AppExtensionCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: AppExtension;
};

export type AppExtensionFilterInput = {
  mount?: InputMaybe<Array<AppExtensionMountEnum>>;
  target?: InputMaybe<AppExtensionTargetEnum>;
};

/** All places where app extension can be mounted. */
export enum AppExtensionMountEnum {
  CustomerDetailsMoreActions = 'CUSTOMER_DETAILS_MORE_ACTIONS',
  CustomerOverviewCreate = 'CUSTOMER_OVERVIEW_CREATE',
  CustomerOverviewMoreActions = 'CUSTOMER_OVERVIEW_MORE_ACTIONS',
  NavigationCatalog = 'NAVIGATION_CATALOG',
  NavigationCustomers = 'NAVIGATION_CUSTOMERS',
  NavigationDiscounts = 'NAVIGATION_DISCOUNTS',
  NavigationOrders = 'NAVIGATION_ORDERS',
  NavigationPages = 'NAVIGATION_PAGES',
  NavigationTranslations = 'NAVIGATION_TRANSLATIONS',
  OrderDetailsMoreActions = 'ORDER_DETAILS_MORE_ACTIONS',
  OrderOverviewCreate = 'ORDER_OVERVIEW_CREATE',
  OrderOverviewMoreActions = 'ORDER_OVERVIEW_MORE_ACTIONS',
  ProductDetailsMoreActions = 'PRODUCT_DETAILS_MORE_ACTIONS',
  ProductOverviewCreate = 'PRODUCT_OVERVIEW_CREATE',
  ProductOverviewMoreActions = 'PRODUCT_OVERVIEW_MORE_ACTIONS'
}

/**
 * All available ways of opening an app extension.
 *
 *     POPUP - app's extension will be mounted as a popup window
 *     APP_PAGE - redirect to app's page
 *
 */
export enum AppExtensionTargetEnum {
  AppPage = 'APP_PAGE',
  Popup = 'POPUP'
}

/**
 * Fetch and validate manifest.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppFetchManifest = {
  __typename?: 'AppFetchManifest';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
  manifest?: Maybe<Manifest>;
};

export type AppFilterInput = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  type?: InputMaybe<AppTypeEnum>;
};

export type AppInput = {
  /** Name of the app. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** List of permission code names to assign to this app. */
  permissions?: InputMaybe<Array<PermissionEnum>>;
};

/** Install new app by using app manifest. Requires the following permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS. */
export type AppInstall = {
  __typename?: 'AppInstall';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  appInstallation?: Maybe<AppInstallation>;
  errors: Array<AppError>;
};

export type AppInstallInput = {
  /** Determine if app will be set active or not. */
  activateAfterInstallation?: InputMaybe<Scalars['Boolean']['input']>;
  /** Name of the app to install. */
  appName?: InputMaybe<Scalars['String']['input']>;
  /** Url to app's manifest in JSON format. */
  manifestUrl?: InputMaybe<Scalars['String']['input']>;
  /** List of permission code names to assign to this app. */
  permissions?: InputMaybe<Array<PermissionEnum>>;
};

/** Represents ongoing installation of app. */
export type AppInstallation = Job & Node & {
  __typename?: 'AppInstallation';
  appName: Scalars['String']['output'];
  /** Created date time of job in ISO 8601 format. */
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  manifestUrl: Scalars['String']['output'];
  /** Job message. */
  message?: Maybe<Scalars['String']['output']>;
  /** Job status. */
  status: JobStatusEnum;
  /** Date time of job last update in ISO 8601 format. */
  updatedAt: Scalars['DateTime']['output'];
};

/**
 * Event sent when new app is installed.
 *
 * Added in Saleor 3.4.
 */
export type AppInstalled = Event & {
  __typename?: 'AppInstalled';
  /** The application the event relates to. */
  app?: Maybe<App>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type AppManifestExtension = {
  __typename?: 'AppManifestExtension';
  /** Label of the extension to show in the dashboard. */
  label: Scalars['String']['output'];
  /** Place where given extension will be mounted. */
  mount: AppExtensionMountEnum;
  /** List of the app extension's permissions. */
  permissions: Array<Permission>;
  /** Type of way how app extension will be opened. */
  target: AppExtensionTargetEnum;
  /** URL of a view where extension's iframe is placed. */
  url: Scalars['String']['output'];
};

export type AppManifestRequiredSaleorVersion = {
  __typename?: 'AppManifestRequiredSaleorVersion';
  /**
   * Required Saleor version as semver range.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  constraint: Scalars['String']['output'];
  /**
   * Informs if the Saleor version matches the required one.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  satisfied: Scalars['Boolean']['output'];
};

export type AppManifestWebhook = {
  __typename?: 'AppManifestWebhook';
  /** The asynchronous events that webhook wants to subscribe. */
  asyncEvents?: Maybe<Array<WebhookEventTypeAsyncEnum>>;
  /** The name of the webhook. */
  name: Scalars['String']['output'];
  /** Subscription query of a webhook */
  query: Scalars['String']['output'];
  /** The synchronous events that webhook wants to subscribe. */
  syncEvents?: Maybe<Array<WebhookEventTypeSyncEnum>>;
  /** The url to receive the payload. */
  targetUrl: Scalars['String']['output'];
};

/**
 * Retry failed installation of new app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppRetryInstall = {
  __typename?: 'AppRetryInstall';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  appInstallation?: Maybe<AppInstallation>;
  errors: Array<AppError>;
};

export enum AppSortField {
  /** Sort apps by creation date. */
  CreationDate = 'CREATION_DATE',
  /** Sort apps by name. */
  Name = 'NAME'
}

export type AppSortingInput = {
  /** Specifies the direction in which to sort apps. */
  direction: OrderDirection;
  /** Sort apps by the selected field. */
  field: AppSortField;
};

/**
 * Event sent when app status has changed.
 *
 * Added in Saleor 3.4.
 */
export type AppStatusChanged = Event & {
  __typename?: 'AppStatusChanged';
  /** The application the event relates to. */
  app?: Maybe<App>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents token data. */
export type AppToken = Node & {
  __typename?: 'AppToken';
  /** Last 4 characters of the token. */
  authToken?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Name of the authenticated token. */
  name?: Maybe<Scalars['String']['output']>;
};

/**
 * Creates a new token.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppTokenCreate = {
  __typename?: 'AppTokenCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  appToken?: Maybe<AppToken>;
  /** The newly created authentication token. */
  authToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AppError>;
};

/**
 * Deletes an authentication token assigned to app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppTokenDelete = {
  __typename?: 'AppTokenDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  appToken?: Maybe<AppToken>;
  errors: Array<AppError>;
};

export type AppTokenInput = {
  /** ID of app. */
  app: Scalars['ID']['input'];
  /** Name of the token. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/** Verify provided app token. */
export type AppTokenVerify = {
  __typename?: 'AppTokenVerify';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
  /** Determine if token is valid or not. */
  valid: Scalars['Boolean']['output'];
};

/** Enum determining type of your App. */
export enum AppTypeEnum {
  /** Local Saleor App. The app is fully manageable from dashboard. You can change assigned permissions, add webhooks, or authentication token */
  Local = 'LOCAL',
  /** Third party external App. Installation is fully automated. Saleor uses a defined App manifest to gather all required information. */
  Thirdparty = 'THIRDPARTY'
}

/**
 * Updates an existing app.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type AppUpdate = {
  __typename?: 'AppUpdate';
  app?: Maybe<App>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  appErrors: Array<AppError>;
  errors: Array<AppError>;
};

/**
 * Event sent when app is updated.
 *
 * Added in Saleor 3.4.
 */
export type AppUpdated = Event & {
  __typename?: 'AppUpdated';
  /** The application the event relates to. */
  app?: Maybe<App>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum AreaUnitsEnum {
  SqCm = 'SQ_CM',
  SqFt = 'SQ_FT',
  SqInch = 'SQ_INCH',
  SqKm = 'SQ_KM',
  SqM = 'SQ_M',
  SqYd = 'SQ_YD'
}

/**
 * Assigns storefront's navigation menus.
 *
 * Requires one of the following permissions: MANAGE_MENUS, MANAGE_SETTINGS.
 */
export type AssignNavigation = {
  __typename?: 'AssignNavigation';
  errors: Array<MenuError>;
  /** Assigned navigation menu. */
  menu?: Maybe<Menu>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

/**
 * Represents assigned attribute to variant with variant selection attached.
 *
 * Added in Saleor 3.1.
 */
export type AssignedVariantAttribute = {
  __typename?: 'AssignedVariantAttribute';
  /** Attribute assigned to variant. */
  attribute: Attribute;
  /** Determines, whether assigned attribute is allowed for variant selection. Supported variant types for variant selection are: ['dropdown', 'boolean', 'swatch', 'numeric'] */
  variantSelection: Scalars['Boolean']['output'];
};

/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type Attribute = Node & ObjectWithMetadata & {
  __typename?: 'Attribute';
  /**
   * Whether the attribute can be displayed in the admin product list. Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  availableInGrid: Scalars['Boolean']['output'];
  /** List of attribute's values. */
  choices?: Maybe<AttributeValueCountableConnection>;
  /** The entity type which can be used as a reference. */
  entityType?: Maybe<AttributeEntityTypeEnum>;
  /**
   * External ID of this attribute.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  /** Whether the attribute can be filtered in dashboard. Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES. */
  filterableInDashboard: Scalars['Boolean']['output'];
  /**
   * Whether the attribute can be filtered in storefront. Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  filterableInStorefront: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  /** The input type to use for entering attribute values in the dashboard. */
  inputType?: Maybe<AttributeInputTypeEnum>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Name of an attribute displayed in the interface. */
  name?: Maybe<Scalars['String']['output']>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  productTypes: ProductTypeCountableConnection;
  productVariantTypes: ProductTypeCountableConnection;
  /** Internal representation of an attribute name. */
  slug?: Maybe<Scalars['String']['output']>;
  /**
   * The position of the attribute in the storefront navigation (0 by default). Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  storefrontSearchPosition: Scalars['Int']['output'];
  /** Returns translated attribute fields for the given language code. */
  translation?: Maybe<AttributeTranslation>;
  /** The attribute type. */
  type?: Maybe<AttributeTypeEnum>;
  /** The unit of attribute values. */
  unit?: Maybe<MeasurementUnitsEnum>;
  /** Whether the attribute requires values to be passed or not. Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES. */
  valueRequired: Scalars['Boolean']['output'];
  /** Whether the attribute should be visible or not in storefront. Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES, MANAGE_PRODUCTS, MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES. */
  visibleInStorefront: Scalars['Boolean']['output'];
  /** Flag indicating that attribute has predefined choices. */
  withChoices: Scalars['Boolean']['output'];
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeChoicesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AttributeValueFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<AttributeChoicesSortingInput>;
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeProductTypesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeProductVariantTypesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Custom attribute of a product. Attributes can be assigned to products and variants at the product type level. */
export type AttributeTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Deletes attributes.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type AttributeBulkDelete = {
  __typename?: 'AttributeBulkDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<AttributeError>;
};

export enum AttributeChoicesSortField {
  /** Sort attribute choice by name. */
  Name = 'NAME',
  /** Sort attribute choice by slug. */
  Slug = 'SLUG'
}

export type AttributeChoicesSortingInput = {
  /** Specifies the direction in which to sort attribute choices. */
  direction: OrderDirection;
  /** Sort attribute choices by the selected field. */
  field: AttributeChoicesSortField;
};

export type AttributeCountableConnection = {
  __typename?: 'AttributeCountableConnection';
  edges: Array<AttributeCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type AttributeCountableEdge = {
  __typename?: 'AttributeCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Attribute;
};

/** Creates an attribute. */
export type AttributeCreate = {
  __typename?: 'AttributeCreate';
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  errors: Array<AttributeError>;
};

export type AttributeCreateInput = {
  /**
   * Whether the attribute can be displayed in the admin product list.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  availableInGrid?: InputMaybe<Scalars['Boolean']['input']>;
  /** The entity type which can be used as a reference. */
  entityType?: InputMaybe<AttributeEntityTypeEnum>;
  /**
   * External ID of this attribute.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Whether the attribute can be filtered in dashboard. */
  filterableInDashboard?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Whether the attribute can be filtered in storefront.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  filterableInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
  /** The input type to use for entering attribute values in the dashboard. */
  inputType?: InputMaybe<AttributeInputTypeEnum>;
  /** Whether the attribute is for variants only. */
  isVariantOnly?: InputMaybe<Scalars['Boolean']['input']>;
  /** Name of an attribute displayed in the interface. */
  name: Scalars['String']['input'];
  /** Internal representation of an attribute name. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /**
   * The position of the attribute in the storefront navigation (0 by default).
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  storefrontSearchPosition?: InputMaybe<Scalars['Int']['input']>;
  /** The attribute type. */
  type: AttributeTypeEnum;
  /** The unit of attribute values. */
  unit?: InputMaybe<MeasurementUnitsEnum>;
  /** Whether the attribute requires values to be passed or not. */
  valueRequired?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of attribute's values. */
  values?: InputMaybe<Array<AttributeValueCreateInput>>;
  /** Whether the attribute should be visible or not in storefront. */
  visibleInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Event sent when new attribute is created.
 *
 * Added in Saleor 3.5.
 */
export type AttributeCreated = Event & {
  __typename?: 'AttributeCreated';
  /** The attribute the event relates to. */
  attribute?: Maybe<Attribute>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes an attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type AttributeDelete = {
  __typename?: 'AttributeDelete';
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  errors: Array<AttributeError>;
};

/**
 * Event sent when attribute is deleted.
 *
 * Added in Saleor 3.5.
 */
export type AttributeDeleted = Event & {
  __typename?: 'AttributeDeleted';
  /** The attribute the event relates to. */
  attribute?: Maybe<Attribute>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum AttributeEntityTypeEnum {
  Page = 'PAGE',
  Product = 'PRODUCT',
  ProductVariant = 'PRODUCT_VARIANT'
}

export type AttributeEntityTypeEnumFilterInput = {
  /** The value equal to. */
  eq?: InputMaybe<AttributeEntityTypeEnum>;
  /** The value included in. */
  oneOf?: InputMaybe<Array<AttributeEntityTypeEnum>>;
};

export type AttributeError = {
  __typename?: 'AttributeError';
  /** The error code. */
  code: AttributeErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum AttributeErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type AttributeFilterInput = {
  availableInGrid?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Specifies the channel by which the data should be filtered.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  filterableInDashboard?: InputMaybe<Scalars['Boolean']['input']>;
  filterableInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  inCategory?: InputMaybe<Scalars['ID']['input']>;
  inCollection?: InputMaybe<Scalars['ID']['input']>;
  isVariantOnly?: InputMaybe<Scalars['Boolean']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
  type?: InputMaybe<AttributeTypeEnum>;
  valueRequired?: InputMaybe<Scalars['Boolean']['input']>;
  visibleInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
};

export type AttributeInput = {
  /** The boolean value of the attribute. */
  boolean?: InputMaybe<Scalars['Boolean']['input']>;
  /** The date range that the returned values should be in. In case of date/time attributes, the UTC midnight of the given date is used. */
  date?: InputMaybe<DateRangeInput>;
  /** The date/time range that the returned values should be in. */
  dateTime?: InputMaybe<DateTimeRangeInput>;
  /** Internal representation of an attribute name. */
  slug: Scalars['String']['input'];
  /** Internal representation of a value (unique per attribute). */
  values?: InputMaybe<Array<Scalars['String']['input']>>;
  /** The range that the returned values should be in. */
  valuesRange?: InputMaybe<IntRangeInput>;
};

/** An enumeration. */
export enum AttributeInputTypeEnum {
  Boolean = 'BOOLEAN',
  Date = 'DATE',
  DateTime = 'DATE_TIME',
  Dropdown = 'DROPDOWN',
  File = 'FILE',
  Multiselect = 'MULTISELECT',
  Numeric = 'NUMERIC',
  PlainText = 'PLAIN_TEXT',
  Reference = 'REFERENCE',
  RichText = 'RICH_TEXT',
  Swatch = 'SWATCH'
}

export type AttributeInputTypeEnumFilterInput = {
  /** The value equal to. */
  eq?: InputMaybe<AttributeInputTypeEnum>;
  /** The value included in. */
  oneOf?: InputMaybe<Array<AttributeInputTypeEnum>>;
};

/**
 * Reorder the values of an attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type AttributeReorderValues = {
  __typename?: 'AttributeReorderValues';
  /** Attribute from which values are reordered. */
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  errors: Array<AttributeError>;
};

export enum AttributeSortField {
  /** Sort attributes based on whether they can be displayed or not in a product grid. */
  AvailableInGrid = 'AVAILABLE_IN_GRID',
  /** Sort attributes by the filterable in dashboard flag */
  FilterableInDashboard = 'FILTERABLE_IN_DASHBOARD',
  /** Sort attributes by the filterable in storefront flag */
  FilterableInStorefront = 'FILTERABLE_IN_STOREFRONT',
  /** Sort attributes by the variant only flag */
  IsVariantOnly = 'IS_VARIANT_ONLY',
  /** Sort attributes by name */
  Name = 'NAME',
  /** Sort attributes by slug */
  Slug = 'SLUG',
  /** Sort attributes by their position in storefront */
  StorefrontSearchPosition = 'STOREFRONT_SEARCH_POSITION',
  /** Sort attributes by the value required flag */
  ValueRequired = 'VALUE_REQUIRED',
  /** Sort attributes by visibility in the storefront */
  VisibleInStorefront = 'VISIBLE_IN_STOREFRONT'
}

export type AttributeSortingInput = {
  /** Specifies the direction in which to sort attributes. */
  direction: OrderDirection;
  /** Sort attributes by the selected field. */
  field: AttributeSortField;
};

export type AttributeTranslatableContent = Node & {
  __typename?: 'AttributeTranslatableContent';
  /**
   * Custom attribute of a product.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  attribute?: Maybe<Attribute>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /** Returns translated attribute fields for the given language code. */
  translation?: Maybe<AttributeTranslation>;
};


export type AttributeTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for an attribute.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type AttributeTranslate = {
  __typename?: 'AttributeTranslate';
  attribute?: Maybe<Attribute>;
  errors: Array<TranslationError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type AttributeTranslation = Node & {
  __typename?: 'AttributeTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name: Scalars['String']['output'];
};

/** An enumeration. */
export enum AttributeTypeEnum {
  PageType = 'PAGE_TYPE',
  ProductType = 'PRODUCT_TYPE'
}

export type AttributeTypeEnumFilterInput = {
  /** The value equal to. */
  eq?: InputMaybe<AttributeTypeEnum>;
  /** The value included in. */
  oneOf?: InputMaybe<Array<AttributeTypeEnum>>;
};

/**
 * Updates attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type AttributeUpdate = {
  __typename?: 'AttributeUpdate';
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  errors: Array<AttributeError>;
};

export type AttributeUpdateInput = {
  /** New values to be created for this attribute. */
  addValues?: InputMaybe<Array<AttributeValueUpdateInput>>;
  /**
   * Whether the attribute can be displayed in the admin product list.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  availableInGrid?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * External ID of this product.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Whether the attribute can be filtered in dashboard. */
  filterableInDashboard?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Whether the attribute can be filtered in storefront.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  filterableInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
  /** Whether the attribute is for variants only. */
  isVariantOnly?: InputMaybe<Scalars['Boolean']['input']>;
  /** Name of an attribute displayed in the interface. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** IDs of values to be removed from this attribute. */
  removeValues?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Internal representation of an attribute name. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /**
   * The position of the attribute in the storefront navigation (0 by default).
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  storefrontSearchPosition?: InputMaybe<Scalars['Int']['input']>;
  /** The unit of attribute values. */
  unit?: InputMaybe<MeasurementUnitsEnum>;
  /** Whether the attribute requires values to be passed or not. */
  valueRequired?: InputMaybe<Scalars['Boolean']['input']>;
  /** Whether the attribute should be visible or not in storefront. */
  visibleInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Event sent when attribute is updated.
 *
 * Added in Saleor 3.5.
 */
export type AttributeUpdated = Event & {
  __typename?: 'AttributeUpdated';
  /** The attribute the event relates to. */
  attribute?: Maybe<Attribute>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents a value of an attribute. */
export type AttributeValue = Node & {
  __typename?: 'AttributeValue';
  /** Represents the boolean value of the attribute value. */
  boolean?: Maybe<Scalars['Boolean']['output']>;
  /** Represents the date value of the attribute value. */
  date?: Maybe<Scalars['Date']['output']>;
  /** Represents the date/time value of the attribute value. */
  dateTime?: Maybe<Scalars['DateTime']['output']>;
  /**
   * External ID of this attribute value.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  /** Represents file URL and content type (if attribute value is a file). */
  file?: Maybe<File>;
  id: Scalars['ID']['output'];
  /** The input type to use for entering attribute values in the dashboard. */
  inputType?: Maybe<AttributeInputTypeEnum>;
  /** Name of a value displayed in the interface. */
  name?: Maybe<Scalars['String']['output']>;
  /** Represents the text of the attribute value, plain text without formating. */
  plainText?: Maybe<Scalars['String']['output']>;
  /** The ID of the attribute reference. */
  reference?: Maybe<Scalars['ID']['output']>;
  /**
   * Represents the text of the attribute value, includes formatting.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  richText?: Maybe<Scalars['JSONString']['output']>;
  /** Internal representation of a value (unique per attribute). */
  slug?: Maybe<Scalars['String']['output']>;
  /** Returns translated attribute value fields for the given language code. */
  translation?: Maybe<AttributeValueTranslation>;
  /** Represent value of the attribute value (e.g. color values for swatch attributes). */
  value?: Maybe<Scalars['String']['output']>;
};


/** Represents a value of an attribute. */
export type AttributeValueTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Deletes values of attributes.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type AttributeValueBulkDelete = {
  __typename?: 'AttributeValueBulkDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<AttributeError>;
};

export type AttributeValueCountableConnection = {
  __typename?: 'AttributeValueCountableConnection';
  edges: Array<AttributeValueCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type AttributeValueCountableEdge = {
  __typename?: 'AttributeValueCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: AttributeValue;
};

/**
 * Creates a value for an attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type AttributeValueCreate = {
  __typename?: 'AttributeValueCreate';
  /** The updated attribute. */
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  attributeValue?: Maybe<AttributeValue>;
  errors: Array<AttributeError>;
};

export type AttributeValueCreateInput = {
  /** File content type. */
  contentType?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of this attribute value.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** URL of the file attribute. Every time, a new value is created. */
  fileUrl?: InputMaybe<Scalars['String']['input']>;
  /** Name of a value displayed in the interface. */
  name: Scalars['String']['input'];
  /**
   * Represents the text of the attribute value, plain text without formating.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.The plain text attribute hasn't got predefined value, so can be specified only from instance that supports the given attribute.
   */
  plainText?: InputMaybe<Scalars['String']['input']>;
  /**
   * Represents the text of the attribute value, includes formatting.
   *
   * Rich text format. For reference see https://editorjs.io/
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.The rich text attribute hasn't got predefined value, so can be specified only from instance that supports the given attribute.
   */
  richText?: InputMaybe<Scalars['JSONString']['input']>;
  /** Represent value of the attribute value (e.g. color values for swatch attributes). */
  value?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new attribute value is created.
 *
 * Added in Saleor 3.5.
 */
export type AttributeValueCreated = Event & {
  __typename?: 'AttributeValueCreated';
  /** The attribute value the event relates to. */
  attributeValue?: Maybe<AttributeValue>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a value of an attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type AttributeValueDelete = {
  __typename?: 'AttributeValueDelete';
  /** The updated attribute. */
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  attributeValue?: Maybe<AttributeValue>;
  errors: Array<AttributeError>;
};

/**
 * Event sent when attribute value is deleted.
 *
 * Added in Saleor 3.5.
 */
export type AttributeValueDeleted = Event & {
  __typename?: 'AttributeValueDeleted';
  /** The attribute value the event relates to. */
  attributeValue?: Maybe<AttributeValue>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type AttributeValueFilterInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  search?: InputMaybe<Scalars['String']['input']>;
};

export type AttributeValueInput = {
  /** Represents the boolean value of the attribute value. */
  boolean?: InputMaybe<Scalars['Boolean']['input']>;
  /** File content type. */
  contentType?: InputMaybe<Scalars['String']['input']>;
  /** Represents the date value of the attribute value. */
  date?: InputMaybe<Scalars['Date']['input']>;
  /** Represents the date/time value of the attribute value. */
  dateTime?: InputMaybe<Scalars['DateTime']['input']>;
  /**
   * Attribute value ID.
   *
   * Added in Saleor 3.9.
   */
  dropdown?: InputMaybe<AttributeValueSelectableTypeInput>;
  /** URL of the file attribute. Every time, a new value is created. */
  file?: InputMaybe<Scalars['String']['input']>;
  /** ID of the selected attribute. */
  id?: InputMaybe<Scalars['ID']['input']>;
  /**
   * List of attribute value IDs.
   *
   * Added in Saleor 3.9.
   */
  multiselect?: InputMaybe<Array<AttributeValueSelectableTypeInput>>;
  /**
   * Numeric value of an attribute.
   *
   * Added in Saleor 3.9.
   */
  numeric?: InputMaybe<Scalars['String']['input']>;
  /** Plain text content. */
  plainText?: InputMaybe<Scalars['String']['input']>;
  /** List of entity IDs that will be used as references. */
  references?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Text content in JSON format. */
  richText?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * Attribute value ID.
   *
   * Added in Saleor 3.9.
   */
  swatch?: InputMaybe<AttributeValueSelectableTypeInput>;
  /** The value or slug of an attribute to resolve. If the passed value is non-existent, it will be created. This field will be removed in Saleor 4.0. */
  values?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Represents attribute value. If no ID provided, value will be resolved.
 *
 * Added in Saleor 3.9.
 */
export type AttributeValueSelectableTypeInput = {
  /** ID of an attribute value. */
  id?: InputMaybe<Scalars['ID']['input']>;
  /** The value or slug of an attribute to resolve. If the passed value is non-existent, it will be created. */
  value?: InputMaybe<Scalars['String']['input']>;
};

export type AttributeValueTranslatableContent = Node & {
  __typename?: 'AttributeValueTranslatableContent';
  /**
   * Associated attribute that can be translated.
   *
   * Added in Saleor 3.9.
   */
  attribute?: Maybe<AttributeTranslatableContent>;
  /**
   * Represents a value of an attribute.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  attributeValue?: Maybe<AttributeValue>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /** Attribute plain text value. */
  plainText?: Maybe<Scalars['String']['output']>;
  /**
   * Attribute value.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  richText?: Maybe<Scalars['JSONString']['output']>;
  /** Returns translated attribute value fields for the given language code. */
  translation?: Maybe<AttributeValueTranslation>;
};


export type AttributeValueTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for an attribute value.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type AttributeValueTranslate = {
  __typename?: 'AttributeValueTranslate';
  attributeValue?: Maybe<AttributeValue>;
  errors: Array<TranslationError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type AttributeValueTranslation = Node & {
  __typename?: 'AttributeValueTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name: Scalars['String']['output'];
  /** Attribute plain text value. */
  plainText?: Maybe<Scalars['String']['output']>;
  /**
   * Attribute value.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  richText?: Maybe<Scalars['JSONString']['output']>;
};

export type AttributeValueTranslationInput = {
  name?: InputMaybe<Scalars['String']['input']>;
  /** Translated text. */
  plainText?: InputMaybe<Scalars['String']['input']>;
  /**
   * Translated text.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  richText?: InputMaybe<Scalars['JSONString']['input']>;
};

/**
 * Updates value of an attribute.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type AttributeValueUpdate = {
  __typename?: 'AttributeValueUpdate';
  /** The updated attribute. */
  attribute?: Maybe<Attribute>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  attributeErrors: Array<AttributeError>;
  attributeValue?: Maybe<AttributeValue>;
  errors: Array<AttributeError>;
};

export type AttributeValueUpdateInput = {
  /** File content type. */
  contentType?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of this attribute value.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** URL of the file attribute. Every time, a new value is created. */
  fileUrl?: InputMaybe<Scalars['String']['input']>;
  /** Name of a value displayed in the interface. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Represents the text of the attribute value, plain text without formating.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.The plain text attribute hasn't got predefined value, so can be specified only from instance that supports the given attribute.
   */
  plainText?: InputMaybe<Scalars['String']['input']>;
  /**
   * Represents the text of the attribute value, includes formatting.
   *
   * Rich text format. For reference see https://editorjs.io/
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.The rich text attribute hasn't got predefined value, so can be specified only from instance that supports the given attribute.
   */
  richText?: InputMaybe<Scalars['JSONString']['input']>;
  /** Represent value of the attribute value (e.g. color values for swatch attributes). */
  value?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when attribute value is updated.
 *
 * Added in Saleor 3.5.
 */
export type AttributeValueUpdated = Event & {
  __typename?: 'AttributeValueUpdated';
  /** The attribute value the event relates to. */
  attributeValue?: Maybe<AttributeValue>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Where filtering options.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type AttributeWhereInput = {
  /** List of conditions that must be met. */
  AND?: InputMaybe<Array<AttributeWhereInput>>;
  /** A list of conditions of which at least one must be met. */
  OR?: InputMaybe<Array<AttributeWhereInput>>;
  entityType?: InputMaybe<AttributeEntityTypeEnumFilterInput>;
  filterableInDashboard?: InputMaybe<Scalars['Boolean']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  inCategory?: InputMaybe<Scalars['ID']['input']>;
  inCollection?: InputMaybe<Scalars['ID']['input']>;
  inputType?: InputMaybe<AttributeInputTypeEnumFilterInput>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  name?: InputMaybe<StringFilterInput>;
  slug?: InputMaybe<StringFilterInput>;
  type?: InputMaybe<AttributeTypeEnumFilterInput>;
  unit?: InputMaybe<MeasurementUnitsEnumFilterInput>;
  valueRequired?: InputMaybe<Scalars['Boolean']['input']>;
  visibleInStorefront?: InputMaybe<Scalars['Boolean']['input']>;
  withChoices?: InputMaybe<Scalars['Boolean']['input']>;
};

export type BulkAttributeValueInput = {
  /** The boolean value of an attribute to resolve. If the passed value is non-existent, it will be created. */
  boolean?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * File content type.
   *
   * Added in Saleor 3.12.
   */
  contentType?: InputMaybe<Scalars['String']['input']>;
  /**
   * Represents the date value of the attribute value.
   *
   * Added in Saleor 3.12.
   */
  date?: InputMaybe<Scalars['Date']['input']>;
  /**
   * Represents the date/time value of the attribute value.
   *
   * Added in Saleor 3.12.
   */
  dateTime?: InputMaybe<Scalars['DateTime']['input']>;
  /**
   * Attribute value ID.
   *
   * Added in Saleor 3.12.
   */
  dropdown?: InputMaybe<AttributeValueSelectableTypeInput>;
  /**
   * URL of the file attribute. Every time, a new value is created.
   *
   * Added in Saleor 3.12.
   */
  file?: InputMaybe<Scalars['String']['input']>;
  /** ID of the selected attribute. */
  id?: InputMaybe<Scalars['ID']['input']>;
  /**
   * List of attribute value IDs.
   *
   * Added in Saleor 3.12.
   */
  multiselect?: InputMaybe<Array<AttributeValueSelectableTypeInput>>;
  /**
   * Numeric value of an attribute.
   *
   * Added in Saleor 3.12.
   */
  numeric?: InputMaybe<Scalars['String']['input']>;
  /**
   * Plain text content.
   *
   * Added in Saleor 3.12.
   */
  plainText?: InputMaybe<Scalars['String']['input']>;
  /**
   * List of entity IDs that will be used as references.
   *
   * Added in Saleor 3.12.
   */
  references?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Text content in JSON format.
   *
   * Added in Saleor 3.12.
   */
  richText?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * Attribute value ID.
   *
   * Added in Saleor 3.12.
   */
  swatch?: InputMaybe<AttributeValueSelectableTypeInput>;
  /** The value or slug of an attribute to resolve. If the passed value is non-existent, it will be created.This field will be removed in Saleor 4.0. */
  values?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type BulkProductError = {
  __typename?: 'BulkProductError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of channel IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** Index of an input list item that caused the error. */
  index?: Maybe<Scalars['Int']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of warehouse IDs which causes the error. */
  warehouses?: Maybe<Array<Scalars['ID']['output']>>;
};

export type BulkStockError = {
  __typename?: 'BulkStockError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** Index of an input list item that caused the error. */
  index?: Maybe<Scalars['Int']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
};

/**
 * Synchronous webhook for calculating checkout/order taxes.
 *
 * Added in Saleor 3.7.
 */
export type CalculateTaxes = Event & {
  __typename?: 'CalculateTaxes';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  taxBase: TaxableObject;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type CardInput = {
  /** Payment method nonce, a token returned by the appropriate provider's SDK. */
  code: Scalars['String']['input'];
  /** Card security code. */
  cvc?: InputMaybe<Scalars['String']['input']>;
  /** Information about currency and amount. */
  money: MoneyInput;
};

export type CatalogueInput = {
  /** Categories related to the discount. */
  categories?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Collections related to the discount. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Products related to the discount. */
  products?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Product variant related to the discount.
   *
   * Added in Saleor 3.1.
   */
  variants?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type Category = Node & ObjectWithMetadata & {
  __typename?: 'Category';
  /** List of ancestors of the category. */
  ancestors?: Maybe<CategoryCountableConnection>;
  backgroundImage?: Maybe<Image>;
  /** List of children of the category. */
  children?: Maybe<CategoryCountableConnection>;
  /**
   * Description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  level: Scalars['Int']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  parent?: Maybe<Category>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of products in the category. Requires the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  products?: Maybe<ProductCountableConnection>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  slug: Scalars['String']['output'];
  /** Returns translated category fields for the given language code. */
  translation?: Maybe<CategoryTranslation>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryAncestorsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryBackgroundImageArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryChildrenArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ProductFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ProductOrder>;
};


/** Represents a single category of products. Categories allow to organize products in a tree-hierarchies which can be used for navigation in the storefront. */
export type CategoryTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Deletes categories.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CategoryBulkDelete = {
  __typename?: 'CategoryBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type CategoryCountableConnection = {
  __typename?: 'CategoryCountableConnection';
  edges: Array<CategoryCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type CategoryCountableEdge = {
  __typename?: 'CategoryCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Category;
};

/**
 * Creates a new category.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CategoryCreate = {
  __typename?: 'CategoryCreate';
  category?: Maybe<Category>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when new category is created.
 *
 * Added in Saleor 3.2.
 */
export type CategoryCreated = Event & {
  __typename?: 'CategoryCreated';
  /** The category the event relates to. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a category.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CategoryDelete = {
  __typename?: 'CategoryDelete';
  category?: Maybe<Category>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when category is deleted.
 *
 * Added in Saleor 3.2.
 */
export type CategoryDeleted = Event & {
  __typename?: 'CategoryDeleted';
  /** The category the event relates to. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type CategoryFilterInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CategoryInput = {
  /** Background image file. */
  backgroundImage?: InputMaybe<Scalars['Upload']['input']>;
  /** Alt text for a product media. */
  backgroundImageAlt?: InputMaybe<Scalars['String']['input']>;
  /**
   * Category description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * Fields required to update the category metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Category name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the category private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Category slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

export enum CategorySortField {
  /** Sort categories by name. */
  Name = 'NAME',
  /** Sort categories by product count. */
  ProductCount = 'PRODUCT_COUNT',
  /** Sort categories by subcategory count. */
  SubcategoryCount = 'SUBCATEGORY_COUNT'
}

export type CategorySortingInput = {
  /**
   * Specifies the channel in which to sort the data.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Specifies the direction in which to sort categories. */
  direction: OrderDirection;
  /** Sort categories by the selected field. */
  field: CategorySortField;
};

export type CategoryTranslatableContent = Node & {
  __typename?: 'CategoryTranslatableContent';
  /**
   * Represents a single category of products.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  category?: Maybe<Category>;
  /**
   * Description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  /** Returns translated category fields for the given language code. */
  translation?: Maybe<CategoryTranslation>;
};


export type CategoryTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a category.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type CategoryTranslate = {
  __typename?: 'CategoryTranslate';
  category?: Maybe<Category>;
  errors: Array<TranslationError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type CategoryTranslation = Node & {
  __typename?: 'CategoryTranslation';
  /**
   * Translated description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Translated description of the category.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
};

/**
 * Updates a category.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CategoryUpdate = {
  __typename?: 'CategoryUpdate';
  category?: Maybe<Category>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when category is updated.
 *
 * Added in Saleor 3.2.
 */
export type CategoryUpdated = Event & {
  __typename?: 'CategoryUpdated';
  /** The category the event relates to. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents channel. */
export type Channel = Node & {
  __typename?: 'Channel';
  /**
   * Shipping methods that are available for the channel.
   *
   * Added in Saleor 3.6.
   */
  availableShippingMethodsPerCountry?: Maybe<Array<ShippingMethodsPerCountry>>;
  /**
   * List of shippable countries for the channel.
   *
   * Added in Saleor 3.6.
   */
  countries?: Maybe<Array<CountryDisplay>>;
  /**
   * A currency that is assigned to the channel.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  currencyCode: Scalars['String']['output'];
  /**
   * Default country for the channel. Default country can be used in checkout to determine the stock quantities or calculate taxes when the country was not explicitly provided.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  defaultCountry: CountryDisplay;
  /**
   * Whether a channel has associated orders.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  hasOrders: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  /**
   * Whether the channel is active.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  isActive: Scalars['Boolean']['output'];
  /**
   * Name of the channel.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  name: Scalars['String']['output'];
  /**
   * Channel-specific order settings.
   *
   * Added in Saleor 3.12.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS, MANAGE_ORDERS.
   */
  orderSettings: OrderSettings;
  /** Slug of the channel. */
  slug: Scalars['String']['output'];
  /**
   * Define the stock setting for this channel.
   *
   * Added in Saleor 3.7.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  stockSettings: StockSettings;
  /**
   * List of warehouses assigned to this channel.
   *
   * Added in Saleor 3.5.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  warehouses: Array<Warehouse>;
};


/** Represents channel. */
export type ChannelAvailableShippingMethodsPerCountryArgs = {
  countries?: InputMaybe<Array<CountryCode>>;
};

/**
 * Activate a channel.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 */
export type ChannelActivate = {
  __typename?: 'ChannelActivate';
  /** Activated channel. */
  channel?: Maybe<Channel>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  channelErrors: Array<ChannelError>;
  errors: Array<ChannelError>;
};

/**
 * Creates new channel.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 */
export type ChannelCreate = {
  __typename?: 'ChannelCreate';
  channel?: Maybe<Channel>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  channelErrors: Array<ChannelError>;
  errors: Array<ChannelError>;
};

export type ChannelCreateInput = {
  /** List of shipping zones to assign to the channel. */
  addShippingZones?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * List of warehouses to assign to the channel.
   *
   * Added in Saleor 3.5.
   */
  addWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Currency of the channel. */
  currencyCode: Scalars['String']['input'];
  /**
   * Default country for the channel. Default country can be used in checkout to determine the stock quantities or calculate taxes when the country was not explicitly provided.
   *
   * Added in Saleor 3.1.
   */
  defaultCountry: CountryCode;
  /** isActive flag. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** Name of the channel. */
  name: Scalars['String']['input'];
  /**
   * The channel order settings
   *
   * Added in Saleor 3.12.
   */
  orderSettings?: InputMaybe<OrderSettingsInput>;
  /** Slug of the channel. */
  slug: Scalars['String']['input'];
  /**
   * The channel stock settings.
   *
   * Added in Saleor 3.7.
   */
  stockSettings?: InputMaybe<StockSettingsInput>;
};

/**
 * Event sent when new channel is created.
 *
 * Added in Saleor 3.2.
 */
export type ChannelCreated = Event & {
  __typename?: 'ChannelCreated';
  /** The channel the event relates to. */
  channel?: Maybe<Channel>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deactivate a channel.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 */
export type ChannelDeactivate = {
  __typename?: 'ChannelDeactivate';
  /** Deactivated channel. */
  channel?: Maybe<Channel>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  channelErrors: Array<ChannelError>;
  errors: Array<ChannelError>;
};

/**
 * Delete a channel. Orders associated with the deleted channel will be moved to the target channel. Checkouts, product availability, and pricing will be removed.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 */
export type ChannelDelete = {
  __typename?: 'ChannelDelete';
  channel?: Maybe<Channel>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  channelErrors: Array<ChannelError>;
  errors: Array<ChannelError>;
};

export type ChannelDeleteInput = {
  /** ID of channel to migrate orders from origin channel. */
  channelId: Scalars['ID']['input'];
};

/**
 * Event sent when channel is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ChannelDeleted = Event & {
  __typename?: 'ChannelDeleted';
  /** The channel the event relates to. */
  channel?: Maybe<Channel>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type ChannelError = {
  __typename?: 'ChannelError';
  /** The error code. */
  code: ChannelErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of shipping zone IDs which causes the error. */
  shippingZones?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of warehouses IDs which causes the error. */
  warehouses?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum ChannelErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  ChannelsCurrencyMustBeTheSame = 'CHANNELS_CURRENCY_MUST_BE_THE_SAME',
  ChannelWithOrders = 'CHANNEL_WITH_ORDERS',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type ChannelListingUpdateInput = {
  /** ID of a channel listing. */
  channelListing: Scalars['ID']['input'];
  /** Cost price of the variant in channel. */
  costPrice?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** The threshold for preorder variant in channel. */
  preorderThreshold?: InputMaybe<Scalars['Int']['input']>;
  /** Price of the particular variant in channel. */
  price?: InputMaybe<Scalars['PositiveDecimal']['input']>;
};

/**
 * Reorder the warehouses of a channel.
 *
 * Added in Saleor 3.7.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 */
export type ChannelReorderWarehouses = {
  __typename?: 'ChannelReorderWarehouses';
  /** Channel within the warehouses are reordered. */
  channel?: Maybe<Channel>;
  errors: Array<ChannelError>;
};

/**
 * Event sent when channel status has changed.
 *
 * Added in Saleor 3.2.
 */
export type ChannelStatusChanged = Event & {
  __typename?: 'ChannelStatusChanged';
  /** The channel the event relates to. */
  channel?: Maybe<Channel>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Update a channel.
 *
 * Requires one of the following permissions: MANAGE_CHANNELS.
 * Requires one of the following permissions when updating only orderSettings field: MANAGE_CHANNELS, MANAGE_ORDERS.
 */
export type ChannelUpdate = {
  __typename?: 'ChannelUpdate';
  channel?: Maybe<Channel>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  channelErrors: Array<ChannelError>;
  errors: Array<ChannelError>;
};

export type ChannelUpdateInput = {
  /** List of shipping zones to assign to the channel. */
  addShippingZones?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * List of warehouses to assign to the channel.
   *
   * Added in Saleor 3.5.
   */
  addWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Default country for the channel. Default country can be used in checkout to determine the stock quantities or calculate taxes when the country was not explicitly provided.
   *
   * Added in Saleor 3.1.
   */
  defaultCountry?: InputMaybe<CountryCode>;
  /** isActive flag. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** Name of the channel. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * The channel order settings
   *
   * Added in Saleor 3.12.
   */
  orderSettings?: InputMaybe<OrderSettingsInput>;
  /** List of shipping zones to unassign from the channel. */
  removeShippingZones?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * List of warehouses to unassign from the channel.
   *
   * Added in Saleor 3.5.
   */
  removeWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Slug of the channel. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /**
   * The channel stock settings.
   *
   * Added in Saleor 3.7.
   */
  stockSettings?: InputMaybe<StockSettingsInput>;
};

/**
 * Event sent when channel is updated.
 *
 * Added in Saleor 3.2.
 */
export type ChannelUpdated = Event & {
  __typename?: 'ChannelUpdated';
  /** The channel the event relates to. */
  channel?: Maybe<Channel>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Checkout object. */
export type Checkout = Node & ObjectWithMetadata & {
  __typename?: 'Checkout';
  /**
   * The authorize status of the checkout.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  authorizeStatus: CheckoutAuthorizeStatusEnum;
  /**
   * Collection points that can be used for this order.
   *
   * Added in Saleor 3.1.
   */
  availableCollectionPoints: Array<Warehouse>;
  /** List of available payment gateways. */
  availablePaymentGateways: Array<PaymentGateway>;
  /**
   * Shipping methods that can be used with this checkout.
   * @deprecated This field will be removed in Saleor 4.0. Use `shippingMethods` instead.
   */
  availableShippingMethods: Array<ShippingMethod>;
  billingAddress?: Maybe<Address>;
  channel: Channel;
  /**
   * The charge status of the checkout.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  chargeStatus: CheckoutChargeStatusEnum;
  created: Scalars['DateTime']['output'];
  /**
   * The delivery method selected for this checkout.
   *
   * Added in Saleor 3.1.
   */
  deliveryMethod?: Maybe<DeliveryMethod>;
  discount?: Maybe<Money>;
  discountName?: Maybe<Scalars['String']['output']>;
  /**
   * Determines whether checkout prices should include taxes when displayed in a storefront.
   *
   * Added in Saleor 3.9.
   */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** Email of a customer. */
  email?: Maybe<Scalars['String']['output']>;
  /** List of gift cards associated with this checkout. */
  giftCards: Array<GiftCard>;
  id: Scalars['ID']['output'];
  /** Returns True, if checkout requires shipping. */
  isShippingRequired: Scalars['Boolean']['output'];
  /** Checkout language code. */
  languageCode: LanguageCodeEnum;
  /** @deprecated This field will be removed in Saleor 4.0. Use `updatedAt` instead. */
  lastChange: Scalars['DateTime']['output'];
  /** A list of checkout lines, each containing information about an item in the checkout. */
  lines: Array<CheckoutLine>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  note: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** The number of items purchased. */
  quantity: Scalars['Int']['output'];
  shippingAddress?: Maybe<Address>;
  /**
   * The shipping method related with checkout.
   * @deprecated This field will be removed in Saleor 4.0. Use `deliveryMethod` instead.
   */
  shippingMethod?: Maybe<ShippingMethod>;
  /** Shipping methods that can be used with this checkout. */
  shippingMethods: Array<ShippingMethod>;
  /** The price of the shipping, with all the taxes included. */
  shippingPrice: TaxedMoney;
  /**
   * Date when oldest stock reservation for this checkout expires or null if no stock is reserved.
   *
   * Added in Saleor 3.1.
   */
  stockReservationExpires?: Maybe<Scalars['DateTime']['output']>;
  /** The price of the checkout before shipping, with taxes included. */
  subtotalPrice: TaxedMoney;
  /**
   * Returns True if checkout has to be exempt from taxes.
   *
   * Added in Saleor 3.8.
   */
  taxExemption: Scalars['Boolean']['output'];
  /** The checkout's token. */
  token: Scalars['UUID']['output'];
  /**
   * The difference between the paid and the checkout total amount.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  totalBalance: Money;
  /** The sum of the the checkout line prices, with all the taxes,shipping costs, and discounts included. */
  totalPrice: TaxedMoney;
  /**
   * List of transactions for the checkout. Requires one of the following permissions: MANAGE_CHECKOUTS, HANDLE_PAYMENTS.
   *
   * Added in Saleor 3.4.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  transactions?: Maybe<Array<TransactionItem>>;
  translatedDiscountName?: Maybe<Scalars['String']['output']>;
  /**
   * Time of last modification of the given checkout.
   *
   * Added in Saleor 3.13.
   */
  updatedAt: Scalars['DateTime']['output'];
  user?: Maybe<User>;
  voucherCode?: Maybe<Scalars['String']['output']>;
};


/** Checkout object. */
export type CheckoutMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Checkout object. */
export type CheckoutMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Checkout object. */
export type CheckoutPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Checkout object. */
export type CheckoutPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/** Adds a gift card or a voucher to a checkout. */
export type CheckoutAddPromoCode = {
  __typename?: 'CheckoutAddPromoCode';
  /** The checkout with the added gift card or voucher. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

export type CheckoutAddressValidationRules = {
  /** Determines if an error should be raised when the provided address doesn't match the expected format. Example: using letters for postal code when the numbers are expected. */
  checkFieldsFormat?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if an error should be raised when the provided address doesn't have all the required fields. The list of required fields is dynamic and depends on the country code (use the `addressValidationRules` query to fetch them). Note: country code is mandatory for all addresses regardless of the rules provided in this input. */
  checkRequiredFields?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if Saleor should apply normalization on address fields. Example: converting city field to uppercase letters. */
  enableFieldsNormalization?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Determine a current authorize status for checkout.
 *
 *     We treat the checkout as fully authorized when the sum of authorized and charged
 *     funds cover the checkout.total.
 *     We treat the checkout as partially authorized when the sum of authorized and charged
 *     funds covers only part of the checkout.total
 *     We treat the checkout as not authorized when the sum of authorized and charged funds
 *     is 0.
 *
 *     NONE - the funds are not authorized
 *     PARTIAL - the cover funds don't cover fully the checkout's total
 *     FULL - the cover funds covers the checkout's total
 *
 */
export enum CheckoutAuthorizeStatusEnum {
  Full = 'FULL',
  None = 'NONE',
  Partial = 'PARTIAL'
}

/** Update billing address in the existing checkout. */
export type CheckoutBillingAddressUpdate = {
  __typename?: 'CheckoutBillingAddressUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/**
 * Determine the current charge status for the checkout.
 *
 *     The checkout is considered overcharged when the sum of the transactionItem's charge
 *     amounts exceeds the value of `checkout.total`.
 *     If the sum of the transactionItem's charge amounts equals
 *     `checkout.total`, we consider the checkout to be fully charged.
 *     If the sum of the transactionItem's charge amounts covers a part of the
 *     `checkout.total`, we treat the checkout as partially charged.
 *
 *
 *     NONE - the funds are not charged.
 *     PARTIAL - the funds that are charged don't cover the checkout's total
 *     FULL - the funds that are charged fully cover the checkout's total
 *     OVERCHARGED - the charged funds are bigger than checkout's total
 *
 */
export enum CheckoutChargeStatusEnum {
  Full = 'FULL',
  None = 'NONE',
  Overcharged = 'OVERCHARGED',
  Partial = 'PARTIAL'
}

/** Completes the checkout. As a result a new order is created and a payment charge is made. This action requires a successful payment before it can be performed. In case additional confirmation step as 3D secure is required confirmationNeeded flag will be set to True and no order created until payment is confirmed with second call of this mutation. */
export type CheckoutComplete = {
  __typename?: 'CheckoutComplete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  /** Confirmation data used to process additional authorization steps. */
  confirmationData?: Maybe<Scalars['JSONString']['output']>;
  /** Set to true if payment needs to be confirmed before checkout is complete. */
  confirmationNeeded: Scalars['Boolean']['output'];
  errors: Array<CheckoutError>;
  /** Placed order. */
  order?: Maybe<Order>;
};

export type CheckoutCountableConnection = {
  __typename?: 'CheckoutCountableConnection';
  edges: Array<CheckoutCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type CheckoutCountableEdge = {
  __typename?: 'CheckoutCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Checkout;
};

/** Create a new checkout. */
export type CheckoutCreate = {
  __typename?: 'CheckoutCreate';
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  /**
   * Whether the checkout was created or the current active one was returned. Refer to checkoutLinesAdd and checkoutLinesUpdate to merge a cart with an active checkout.
   * @deprecated This field will be removed in Saleor 4.0. Always returns `true`.
   */
  created?: Maybe<Scalars['Boolean']['output']>;
  errors: Array<CheckoutError>;
};

/**
 * Create new checkout from existing order.
 *
 * Added in Saleor 3.14.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type CheckoutCreateFromOrder = {
  __typename?: 'CheckoutCreateFromOrder';
  /** Created checkout. */
  checkout?: Maybe<Checkout>;
  errors: Array<CheckoutCreateFromOrderError>;
  /** Variants that were not attached to the checkout. */
  unavailableVariants?: Maybe<Array<CheckoutCreateFromOrderUnavailableVariant>>;
};

export type CheckoutCreateFromOrderError = {
  __typename?: 'CheckoutCreateFromOrderError';
  /** The error code. */
  code: CheckoutCreateFromOrderErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum CheckoutCreateFromOrderErrorCode {
  ChannelInactive = 'CHANNEL_INACTIVE',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  OrderNotFound = 'ORDER_NOT_FOUND',
  TaxError = 'TAX_ERROR'
}

export type CheckoutCreateFromOrderUnavailableVariant = {
  __typename?: 'CheckoutCreateFromOrderUnavailableVariant';
  /** The error code. */
  code: CheckoutCreateFromOrderUnavailableVariantErrorCode;
  /** Order line ID that is unavailable. */
  lineId: Scalars['ID']['output'];
  /** The error message. */
  message: Scalars['String']['output'];
  /** Variant ID that is unavailable. */
  variantId: Scalars['ID']['output'];
};

/** An enumeration. */
export enum CheckoutCreateFromOrderUnavailableVariantErrorCode {
  InsufficientStock = 'INSUFFICIENT_STOCK',
  NotFound = 'NOT_FOUND',
  ProductNotPublished = 'PRODUCT_NOT_PUBLISHED',
  ProductUnavailableForPurchase = 'PRODUCT_UNAVAILABLE_FOR_PURCHASE',
  QuantityGreaterThanLimit = 'QUANTITY_GREATER_THAN_LIMIT',
  UnavailableVariantInChannel = 'UNAVAILABLE_VARIANT_IN_CHANNEL'
}

export type CheckoutCreateInput = {
  /** Billing address of the customer. */
  billingAddress?: InputMaybe<AddressInput>;
  /** Slug of a channel in which to create a checkout. */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** The customer's email address. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** Checkout language code. */
  languageCode?: InputMaybe<LanguageCodeEnum>;
  /** A list of checkout lines, each containing information about an item in the checkout. */
  lines: Array<CheckoutLineInput>;
  /** The mailing address to where the checkout will be shipped. Note: the address will be ignored if the checkout doesn't contain shippable items. */
  shippingAddress?: InputMaybe<AddressInput>;
  /**
   * The checkout validation rules that can be changed.
   *
   * Added in Saleor 3.5.
   */
  validationRules?: InputMaybe<CheckoutValidationRules>;
};

/**
 * Event sent when new checkout is created.
 *
 * Added in Saleor 3.2.
 */
export type CheckoutCreated = Event & {
  __typename?: 'CheckoutCreated';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Sets the customer as the owner of the checkout.
 *
 * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_USER.
 */
export type CheckoutCustomerAttach = {
  __typename?: 'CheckoutCustomerAttach';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/**
 * Removes the user assigned as the owner of the checkout.
 *
 * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_USER.
 */
export type CheckoutCustomerDetach = {
  __typename?: 'CheckoutCustomerDetach';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/**
 * Updates the delivery method (shipping method or pick up point) of the checkout.
 *
 * Added in Saleor 3.1.
 */
export type CheckoutDeliveryMethodUpdate = {
  __typename?: 'CheckoutDeliveryMethodUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  errors: Array<CheckoutError>;
};

/** Updates email address in the existing checkout object. */
export type CheckoutEmailUpdate = {
  __typename?: 'CheckoutEmailUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

export type CheckoutError = {
  __typename?: 'CheckoutError';
  /** A type of address that causes the error. */
  addressType?: Maybe<AddressTypeEnum>;
  /** The error code. */
  code: CheckoutErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** List of line Ids which cause the error. */
  lines?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of varint IDs which causes the error. */
  variants?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum CheckoutErrorCode {
  BillingAddressNotSet = 'BILLING_ADDRESS_NOT_SET',
  ChannelInactive = 'CHANNEL_INACTIVE',
  CheckoutNotFullyPaid = 'CHECKOUT_NOT_FULLY_PAID',
  DeliveryMethodNotApplicable = 'DELIVERY_METHOD_NOT_APPLICABLE',
  EmailNotSet = 'EMAIL_NOT_SET',
  GiftCardNotApplicable = 'GIFT_CARD_NOT_APPLICABLE',
  GraphqlError = 'GRAPHQL_ERROR',
  InactivePayment = 'INACTIVE_PAYMENT',
  InsufficientStock = 'INSUFFICIENT_STOCK',
  Invalid = 'INVALID',
  InvalidShippingMethod = 'INVALID_SHIPPING_METHOD',
  MissingChannelSlug = 'MISSING_CHANNEL_SLUG',
  NotFound = 'NOT_FOUND',
  NoLines = 'NO_LINES',
  PaymentError = 'PAYMENT_ERROR',
  ProductNotPublished = 'PRODUCT_NOT_PUBLISHED',
  ProductUnavailableForPurchase = 'PRODUCT_UNAVAILABLE_FOR_PURCHASE',
  QuantityGreaterThanLimit = 'QUANTITY_GREATER_THAN_LIMIT',
  Required = 'REQUIRED',
  ShippingAddressNotSet = 'SHIPPING_ADDRESS_NOT_SET',
  ShippingMethodNotApplicable = 'SHIPPING_METHOD_NOT_APPLICABLE',
  ShippingMethodNotSet = 'SHIPPING_METHOD_NOT_SET',
  ShippingNotRequired = 'SHIPPING_NOT_REQUIRED',
  TaxError = 'TAX_ERROR',
  UnavailableVariantInChannel = 'UNAVAILABLE_VARIANT_IN_CHANNEL',
  Unique = 'UNIQUE',
  VoucherNotApplicable = 'VOUCHER_NOT_APPLICABLE',
  ZeroQuantity = 'ZERO_QUANTITY'
}

export type CheckoutFilterInput = {
  authorizeStatus?: InputMaybe<Array<CheckoutAuthorizeStatusEnum>>;
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  chargeStatus?: InputMaybe<Array<CheckoutChargeStatusEnum>>;
  created?: InputMaybe<DateRangeInput>;
  customer?: InputMaybe<Scalars['String']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  updatedAt?: InputMaybe<DateRangeInput>;
};

/**
 * Filter shipping methods for checkout.
 *
 * Added in Saleor 3.6.
 */
export type CheckoutFilterShippingMethods = Event & {
  __typename?: 'CheckoutFilterShippingMethods';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /**
   * Shipping methods that can be used with this checkout.
   *
   * Added in Saleor 3.6.
   */
  shippingMethods?: Maybe<Array<ShippingMethod>>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when checkout is fully paid with transactions.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type CheckoutFullyPaid = Event & {
  __typename?: 'CheckoutFullyPaid';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Update language code in the existing checkout. */
export type CheckoutLanguageCodeUpdate = {
  __typename?: 'CheckoutLanguageCodeUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/** Represents an item in the checkout. */
export type CheckoutLine = Node & ObjectWithMetadata & {
  __typename?: 'CheckoutLine';
  id: Scalars['ID']['output'];
  /**
   * List of public metadata items. Can be accessed without permissions.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * List of private metadata items. Requires staff permissions to access.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  quantity: Scalars['Int']['output'];
  /** Indicates whether the item need to be delivered. */
  requiresShipping: Scalars['Boolean']['output'];
  /** The sum of the checkout line price, taxes and discounts. */
  totalPrice: TaxedMoney;
  /** The sum of the checkout line price, without discounts. */
  undiscountedTotalPrice: Money;
  /** The unit price of the checkout line, without discounts. */
  undiscountedUnitPrice: Money;
  /** The unit price of the checkout line, with taxes and discounts. */
  unitPrice: TaxedMoney;
  variant: ProductVariant;
};


/** Represents an item in the checkout. */
export type CheckoutLineMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an item in the checkout. */
export type CheckoutLineMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents an item in the checkout. */
export type CheckoutLinePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an item in the checkout. */
export type CheckoutLinePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CheckoutLineCountableConnection = {
  __typename?: 'CheckoutLineCountableConnection';
  edges: Array<CheckoutLineCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type CheckoutLineCountableEdge = {
  __typename?: 'CheckoutLineCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: CheckoutLine;
};

/** Deletes a CheckoutLine. */
export type CheckoutLineDelete = {
  __typename?: 'CheckoutLineDelete';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

export type CheckoutLineInput = {
  /**
   * Flag that allow force splitting the same variant into multiple lines by skipping the matching logic.
   *
   * Added in Saleor 3.6.
   */
  forceNewLine?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Fields required to update the object's metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Custom price of the item. Can be set only by apps with `HANDLE_CHECKOUTS` permission. When the line with the same variant will be provided multiple times, the last price will be used.
   *
   * Added in Saleor 3.1.
   */
  price?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** The number of items purchased. */
  quantity: Scalars['Int']['input'];
  /** ID of the product variant. */
  variantId: Scalars['ID']['input'];
};

export type CheckoutLineUpdateInput = {
  /**
   * ID of the line.
   *
   * Added in Saleor 3.6.
   */
  lineId?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Custom price of the item. Can be set only by apps with `HANDLE_CHECKOUTS` permission. When the line with the same variant will be provided multiple times, the last price will be used.
   *
   * Added in Saleor 3.1.
   */
  price?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** The number of items purchased. Optional for apps, required for any other users. */
  quantity?: InputMaybe<Scalars['Int']['input']>;
  /**
   * ID of the product variant.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `lineId` instead.
   */
  variantId?: InputMaybe<Scalars['ID']['input']>;
};

/** Adds a checkout line to the existing checkout.If line was already in checkout, its quantity will be increased. */
export type CheckoutLinesAdd = {
  __typename?: 'CheckoutLinesAdd';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/** Deletes checkout lines. */
export type CheckoutLinesDelete = {
  __typename?: 'CheckoutLinesDelete';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  errors: Array<CheckoutError>;
};

/** Updates checkout line in the existing checkout. */
export type CheckoutLinesUpdate = {
  __typename?: 'CheckoutLinesUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/**
 * Event sent when checkout metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type CheckoutMetadataUpdated = Event & {
  __typename?: 'CheckoutMetadataUpdated';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Create a new payment for given checkout. */
export type CheckoutPaymentCreate = {
  __typename?: 'CheckoutPaymentCreate';
  /** Related checkout object. */
  checkout?: Maybe<Checkout>;
  errors: Array<PaymentError>;
  /** A newly created payment. */
  payment?: Maybe<Payment>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

/** Remove a gift card or a voucher from a checkout. */
export type CheckoutRemovePromoCode = {
  __typename?: 'CheckoutRemovePromoCode';
  /** The checkout with the removed gift card or voucher. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/** Update shipping address in the existing checkout. */
export type CheckoutShippingAddressUpdate = {
  __typename?: 'CheckoutShippingAddressUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

/** Updates the shipping method of the checkout. */
export type CheckoutShippingMethodUpdate = {
  __typename?: 'CheckoutShippingMethodUpdate';
  /** An updated checkout. */
  checkout?: Maybe<Checkout>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  checkoutErrors: Array<CheckoutError>;
  errors: Array<CheckoutError>;
};

export enum CheckoutSortField {
  /** Sort checkouts by creation date. */
  CreationDate = 'CREATION_DATE',
  /** Sort checkouts by customer. */
  Customer = 'CUSTOMER',
  /** Sort checkouts by payment. */
  Payment = 'PAYMENT'
}

export type CheckoutSortingInput = {
  /** Specifies the direction in which to sort checkouts. */
  direction: OrderDirection;
  /** Sort checkouts by the selected field. */
  field: CheckoutSortField;
};

/**
 * Event sent when checkout is updated.
 *
 * Added in Saleor 3.2.
 */
export type CheckoutUpdated = Event & {
  __typename?: 'CheckoutUpdated';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type CheckoutValidationRules = {
  /** The validation rules that can be applied to provided billing address data. */
  billingAddress?: InputMaybe<CheckoutAddressValidationRules>;
  /** The validation rules that can be applied to provided shipping address data. */
  shippingAddress?: InputMaybe<CheckoutAddressValidationRules>;
};

export type ChoiceValue = {
  __typename?: 'ChoiceValue';
  raw?: Maybe<Scalars['String']['output']>;
  verbose?: Maybe<Scalars['String']['output']>;
};

/** Represents a collection of products. */
export type Collection = Node & ObjectWithMetadata & {
  __typename?: 'Collection';
  backgroundImage?: Maybe<Image>;
  /** Channel given to retrieve this collection. Also used by federation gateway to resolve this object in a federated query. */
  channel?: Maybe<Scalars['String']['output']>;
  /**
   * List of channels in which the collection is available.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  channelListings?: Maybe<Array<CollectionChannelListing>>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of products in this collection. */
  products?: Maybe<ProductCountableConnection>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  slug: Scalars['String']['output'];
  /** Returns translated collection fields for the given language code. */
  translation?: Maybe<CollectionTranslation>;
};


/** Represents a collection of products. */
export type CollectionBackgroundImageArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents a collection of products. */
export type CollectionMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a collection of products. */
export type CollectionMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a collection of products. */
export type CollectionPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a collection of products. */
export type CollectionPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a collection of products. */
export type CollectionProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ProductFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ProductOrder>;
};


/** Represents a collection of products. */
export type CollectionTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Adds products to a collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionAddProducts = {
  __typename?: 'CollectionAddProducts';
  /** Collection to which products will be added. */
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

/**
 * Deletes collections.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionBulkDelete = {
  __typename?: 'CollectionBulkDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<CollectionError>;
};

/** Represents collection channel listing. */
export type CollectionChannelListing = Node & {
  __typename?: 'CollectionChannelListing';
  channel: Channel;
  id: Scalars['ID']['output'];
  isPublished: Scalars['Boolean']['output'];
  /** @deprecated This field will be removed in Saleor 4.0. Use the `publishedAt` field to fetch the publication date. */
  publicationDate?: Maybe<Scalars['Date']['output']>;
  /**
   * The collection publication date.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
};

export type CollectionChannelListingError = {
  __typename?: 'CollectionChannelListingError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of channels IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
};

/**
 * Manage collection's availability in channels.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionChannelListingUpdate = {
  __typename?: 'CollectionChannelListingUpdate';
  /** An updated collection instance. */
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionChannelListingErrors: Array<CollectionChannelListingError>;
  errors: Array<CollectionChannelListingError>;
};

export type CollectionChannelListingUpdateInput = {
  /** List of channels to which the collection should be assigned. */
  addChannels?: InputMaybe<Array<PublishableChannelListingInput>>;
  /** List of channels from which the collection should be unassigned. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
};

export type CollectionCountableConnection = {
  __typename?: 'CollectionCountableConnection';
  edges: Array<CollectionCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type CollectionCountableEdge = {
  __typename?: 'CollectionCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Collection;
};

/**
 * Creates a new collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionCreate = {
  __typename?: 'CollectionCreate';
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

export type CollectionCreateInput = {
  /** Background image file. */
  backgroundImage?: InputMaybe<Scalars['Upload']['input']>;
  /** Alt text for an image. */
  backgroundImageAlt?: InputMaybe<Scalars['String']['input']>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /** Informs whether a collection is published. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Fields required to update the collection metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Name of the collection. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the collection private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** List of products to be added to the collection. */
  products?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  publicationDate?: InputMaybe<Scalars['Date']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Slug of the collection. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new collection is created.
 *
 * Added in Saleor 3.2.
 */
export type CollectionCreated = Event & {
  __typename?: 'CollectionCreated';
  /** The collection the event relates to. */
  collection?: Maybe<Collection>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new collection is created.
 *
 * Added in Saleor 3.2.
 */
export type CollectionCreatedCollectionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionDelete = {
  __typename?: 'CollectionDelete';
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

/**
 * Event sent when collection is deleted.
 *
 * Added in Saleor 3.2.
 */
export type CollectionDeleted = Event & {
  __typename?: 'CollectionDeleted';
  /** The collection the event relates to. */
  collection?: Maybe<Collection>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when collection is deleted.
 *
 * Added in Saleor 3.2.
 */
export type CollectionDeletedCollectionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type CollectionError = {
  __typename?: 'CollectionError';
  /** The error code. */
  code: CollectionErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of products IDs which causes the error. */
  products?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum CollectionErrorCode {
  CannotManageProductWithoutVariant = 'CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type CollectionFilterInput = {
  /**
   * Specifies the channel by which the data should be filtered.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  published?: InputMaybe<CollectionPublished>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CollectionInput = {
  /** Background image file. */
  backgroundImage?: InputMaybe<Scalars['Upload']['input']>;
  /** Alt text for an image. */
  backgroundImageAlt?: InputMaybe<Scalars['String']['input']>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /** Informs whether a collection is published. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Fields required to update the collection metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Name of the collection. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the collection private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  publicationDate?: InputMaybe<Scalars['Date']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Slug of the collection. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when collection metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type CollectionMetadataUpdated = Event & {
  __typename?: 'CollectionMetadataUpdated';
  /** The collection the event relates to. */
  collection?: Maybe<Collection>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when collection metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type CollectionMetadataUpdatedCollectionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export enum CollectionPublished {
  Hidden = 'HIDDEN',
  Published = 'PUBLISHED'
}

/**
 * Remove products from a collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionRemoveProducts = {
  __typename?: 'CollectionRemoveProducts';
  /** Collection from which products will be removed. */
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

/**
 * Reorder the products of a collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionReorderProducts = {
  __typename?: 'CollectionReorderProducts';
  /** Collection from which products are reordered. */
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

export enum CollectionSortField {
  /**
   * Sort collections by availability.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Availability = 'AVAILABILITY',
  /** Sort collections by name. */
  Name = 'NAME',
  /** Sort collections by product count. */
  ProductCount = 'PRODUCT_COUNT',
  /**
   * Sort collections by publication date.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  PublicationDate = 'PUBLICATION_DATE',
  /**
   * Sort collections by publication date.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  PublishedAt = 'PUBLISHED_AT'
}

export type CollectionSortingInput = {
  /**
   * Specifies the channel in which to sort the data.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Specifies the direction in which to sort collections. */
  direction: OrderDirection;
  /** Sort collections by the selected field. */
  field: CollectionSortField;
};

export type CollectionTranslatableContent = Node & {
  __typename?: 'CollectionTranslatableContent';
  /**
   * Represents a collection of products.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  collection?: Maybe<Collection>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  /** Returns translated collection fields for the given language code. */
  translation?: Maybe<CollectionTranslation>;
};


export type CollectionTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a collection.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type CollectionTranslate = {
  __typename?: 'CollectionTranslate';
  collection?: Maybe<Collection>;
  errors: Array<TranslationError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type CollectionTranslation = Node & {
  __typename?: 'CollectionTranslation';
  /**
   * Translated description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Translated description of the collection.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
};

/**
 * Updates a collection.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type CollectionUpdate = {
  __typename?: 'CollectionUpdate';
  collection?: Maybe<Collection>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  collectionErrors: Array<CollectionError>;
  errors: Array<CollectionError>;
};

/**
 * Event sent when collection is updated.
 *
 * Added in Saleor 3.2.
 */
export type CollectionUpdated = Event & {
  __typename?: 'CollectionUpdated';
  /** The collection the event relates to. */
  collection?: Maybe<Collection>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when collection is updated.
 *
 * Added in Saleor 3.2.
 */
export type CollectionUpdatedCollectionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Stores information about a single configuration field. */
export type ConfigurationItem = {
  __typename?: 'ConfigurationItem';
  /** Help text for the field. */
  helpText?: Maybe<Scalars['String']['output']>;
  /** Label for the field. */
  label?: Maybe<Scalars['String']['output']>;
  /** Name of the field. */
  name: Scalars['String']['output'];
  /** Type of the field. */
  type?: Maybe<ConfigurationTypeFieldEnum>;
  /** Current value of the field. */
  value?: Maybe<Scalars['String']['output']>;
};

export type ConfigurationItemInput = {
  /** Name of the field to update. */
  name: Scalars['String']['input'];
  /** Value of the given field to update. */
  value?: InputMaybe<Scalars['String']['input']>;
};

/** An enumeration. */
export enum ConfigurationTypeFieldEnum {
  Boolean = 'BOOLEAN',
  Multiline = 'MULTILINE',
  Output = 'OUTPUT',
  Password = 'PASSWORD',
  Secret = 'SECRET',
  Secretmultiline = 'SECRETMULTILINE',
  String = 'STRING'
}

/** Confirm user account with token sent by email during registration. */
export type ConfirmAccount = {
  __typename?: 'ConfirmAccount';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** An activated user account. */
  user?: Maybe<User>;
};

/**
 * Confirm the email change of the logged-in user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type ConfirmEmailChange = {
  __typename?: 'ConfirmEmailChange';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** A user instance with a new email. */
  user?: Maybe<User>;
};

/** An enumeration. */
export enum CountryCode {
  Ad = 'AD',
  Ae = 'AE',
  Af = 'AF',
  Ag = 'AG',
  Ai = 'AI',
  Al = 'AL',
  Am = 'AM',
  Ao = 'AO',
  Aq = 'AQ',
  Ar = 'AR',
  As = 'AS',
  At = 'AT',
  Au = 'AU',
  Aw = 'AW',
  Ax = 'AX',
  Az = 'AZ',
  Ba = 'BA',
  Bb = 'BB',
  Bd = 'BD',
  Be = 'BE',
  Bf = 'BF',
  Bg = 'BG',
  Bh = 'BH',
  Bi = 'BI',
  Bj = 'BJ',
  Bl = 'BL',
  Bm = 'BM',
  Bn = 'BN',
  Bo = 'BO',
  Bq = 'BQ',
  Br = 'BR',
  Bs = 'BS',
  Bt = 'BT',
  Bv = 'BV',
  Bw = 'BW',
  By = 'BY',
  Bz = 'BZ',
  Ca = 'CA',
  Cc = 'CC',
  Cd = 'CD',
  Cf = 'CF',
  Cg = 'CG',
  Ch = 'CH',
  Ci = 'CI',
  Ck = 'CK',
  Cl = 'CL',
  Cm = 'CM',
  Cn = 'CN',
  Co = 'CO',
  Cr = 'CR',
  Cu = 'CU',
  Cv = 'CV',
  Cw = 'CW',
  Cx = 'CX',
  Cy = 'CY',
  Cz = 'CZ',
  De = 'DE',
  Dj = 'DJ',
  Dk = 'DK',
  Dm = 'DM',
  Do = 'DO',
  Dz = 'DZ',
  Ec = 'EC',
  Ee = 'EE',
  Eg = 'EG',
  Eh = 'EH',
  Er = 'ER',
  Es = 'ES',
  Et = 'ET',
  Eu = 'EU',
  Fi = 'FI',
  Fj = 'FJ',
  Fk = 'FK',
  Fm = 'FM',
  Fo = 'FO',
  Fr = 'FR',
  Ga = 'GA',
  Gb = 'GB',
  Gd = 'GD',
  Ge = 'GE',
  Gf = 'GF',
  Gg = 'GG',
  Gh = 'GH',
  Gi = 'GI',
  Gl = 'GL',
  Gm = 'GM',
  Gn = 'GN',
  Gp = 'GP',
  Gq = 'GQ',
  Gr = 'GR',
  Gs = 'GS',
  Gt = 'GT',
  Gu = 'GU',
  Gw = 'GW',
  Gy = 'GY',
  Hk = 'HK',
  Hm = 'HM',
  Hn = 'HN',
  Hr = 'HR',
  Ht = 'HT',
  Hu = 'HU',
  Id = 'ID',
  Ie = 'IE',
  Il = 'IL',
  Im = 'IM',
  In = 'IN',
  Io = 'IO',
  Iq = 'IQ',
  Ir = 'IR',
  Is = 'IS',
  It = 'IT',
  Je = 'JE',
  Jm = 'JM',
  Jo = 'JO',
  Jp = 'JP',
  Ke = 'KE',
  Kg = 'KG',
  Kh = 'KH',
  Ki = 'KI',
  Km = 'KM',
  Kn = 'KN',
  Kp = 'KP',
  Kr = 'KR',
  Kw = 'KW',
  Ky = 'KY',
  Kz = 'KZ',
  La = 'LA',
  Lb = 'LB',
  Lc = 'LC',
  Li = 'LI',
  Lk = 'LK',
  Lr = 'LR',
  Ls = 'LS',
  Lt = 'LT',
  Lu = 'LU',
  Lv = 'LV',
  Ly = 'LY',
  Ma = 'MA',
  Mc = 'MC',
  Md = 'MD',
  Me = 'ME',
  Mf = 'MF',
  Mg = 'MG',
  Mh = 'MH',
  Mk = 'MK',
  Ml = 'ML',
  Mm = 'MM',
  Mn = 'MN',
  Mo = 'MO',
  Mp = 'MP',
  Mq = 'MQ',
  Mr = 'MR',
  Ms = 'MS',
  Mt = 'MT',
  Mu = 'MU',
  Mv = 'MV',
  Mw = 'MW',
  Mx = 'MX',
  My = 'MY',
  Mz = 'MZ',
  Na = 'NA',
  Nc = 'NC',
  Ne = 'NE',
  Nf = 'NF',
  Ng = 'NG',
  Ni = 'NI',
  Nl = 'NL',
  No = 'NO',
  Np = 'NP',
  Nr = 'NR',
  Nu = 'NU',
  Nz = 'NZ',
  Om = 'OM',
  Pa = 'PA',
  Pe = 'PE',
  Pf = 'PF',
  Pg = 'PG',
  Ph = 'PH',
  Pk = 'PK',
  Pl = 'PL',
  Pm = 'PM',
  Pn = 'PN',
  Pr = 'PR',
  Ps = 'PS',
  Pt = 'PT',
  Pw = 'PW',
  Py = 'PY',
  Qa = 'QA',
  Re = 'RE',
  Ro = 'RO',
  Rs = 'RS',
  Ru = 'RU',
  Rw = 'RW',
  Sa = 'SA',
  Sb = 'SB',
  Sc = 'SC',
  Sd = 'SD',
  Se = 'SE',
  Sg = 'SG',
  Sh = 'SH',
  Si = 'SI',
  Sj = 'SJ',
  Sk = 'SK',
  Sl = 'SL',
  Sm = 'SM',
  Sn = 'SN',
  So = 'SO',
  Sr = 'SR',
  Ss = 'SS',
  St = 'ST',
  Sv = 'SV',
  Sx = 'SX',
  Sy = 'SY',
  Sz = 'SZ',
  Tc = 'TC',
  Td = 'TD',
  Tf = 'TF',
  Tg = 'TG',
  Th = 'TH',
  Tj = 'TJ',
  Tk = 'TK',
  Tl = 'TL',
  Tm = 'TM',
  Tn = 'TN',
  To = 'TO',
  Tr = 'TR',
  Tt = 'TT',
  Tv = 'TV',
  Tw = 'TW',
  Tz = 'TZ',
  Ua = 'UA',
  Ug = 'UG',
  Um = 'UM',
  Us = 'US',
  Uy = 'UY',
  Uz = 'UZ',
  Va = 'VA',
  Vc = 'VC',
  Ve = 'VE',
  Vg = 'VG',
  Vi = 'VI',
  Vn = 'VN',
  Vu = 'VU',
  Wf = 'WF',
  Ws = 'WS',
  Ye = 'YE',
  Yt = 'YT',
  Za = 'ZA',
  Zm = 'ZM',
  Zw = 'ZW'
}

export type CountryDisplay = {
  __typename?: 'CountryDisplay';
  /** Country code. */
  code: Scalars['String']['output'];
  /** Country name. */
  country: Scalars['String']['output'];
  /**
   * Country tax.
   * @deprecated This field will be removed in Saleor 4.0. Use `TaxClassCountryRate` type to manage tax rates per country.
   */
  vat?: Maybe<Vat>;
};

export type CountryFilterInput = {
  /** Boolean for filtering countries by having shipping zone assigned.If 'true', return countries with shipping zone assigned.If 'false', return countries without any shipping zone assigned.If the argument is not provided (null), return all countries. */
  attachedToShippingZones?: InputMaybe<Scalars['Boolean']['input']>;
};

export type CountryRateInput = {
  /** Country in which this rate applies. */
  countryCode: CountryCode;
  /** Tax rate value provided as percentage. Example: provide `23` to represent `23%` tax rate. */
  rate: Scalars['Float']['input'];
};

export type CountryRateUpdateInput = {
  /** Country in which this rate applies. */
  countryCode: CountryCode;
  /** Tax rate value provided as percentage. Example: provide `23` to represent `23%` tax rate. Provide `null` to remove the particular rate. */
  rate?: InputMaybe<Scalars['Float']['input']>;
};

/** Create JWT token. */
export type CreateToken = {
  __typename?: 'CreateToken';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** CSRF token required to re-generate access token. */
  csrfToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AccountError>;
  /** JWT refresh token, required to re-generate access token. */
  refreshToken?: Maybe<Scalars['String']['output']>;
  /** JWT token, required to authenticate. */
  token?: Maybe<Scalars['String']['output']>;
  /** A user instance. */
  user?: Maybe<User>;
};

export type CreditCard = {
  __typename?: 'CreditCard';
  /** Card brand. */
  brand: Scalars['String']['output'];
  /** Two-digit number representing the card’s expiration month. */
  expMonth?: Maybe<Scalars['Int']['output']>;
  /** Four-digit number representing the card’s expiration year. */
  expYear?: Maybe<Scalars['Int']['output']>;
  /** First 4 digits of the card number. */
  firstDigits?: Maybe<Scalars['String']['output']>;
  /** Last 4 digits of the card number. */
  lastDigits: Scalars['String']['output'];
};

/**
 * Deletes customers.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type CustomerBulkDelete = {
  __typename?: 'CustomerBulkDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<AccountError>;
};

export type CustomerBulkResult = {
  __typename?: 'CustomerBulkResult';
  /** Customer data. */
  customer?: Maybe<User>;
  /** List of errors that occurred during the update attempt. */
  errors?: Maybe<Array<CustomerBulkUpdateError>>;
};

/**
 * Updates customers.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type CustomerBulkUpdate = {
  __typename?: 'CustomerBulkUpdate';
  /** Returns how many objects were created. */
  count: Scalars['Int']['output'];
  errors: Array<CustomerBulkUpdateError>;
  /** List of the updated customers. */
  results: Array<CustomerBulkResult>;
};

export type CustomerBulkUpdateError = {
  __typename?: 'CustomerBulkUpdateError';
  /** The error code. */
  code: CustomerBulkUpdateErrorCode;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** Path to field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  path?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum CustomerBulkUpdateErrorCode {
  Blank = 'BLANK',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  MaxLength = 'MAX_LENGTH',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type CustomerBulkUpdateInput = {
  /** External ID of a customer to update. */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** ID of a customer to update. */
  id?: InputMaybe<Scalars['ID']['input']>;
  /** Fields required to update a customer. */
  input: CustomerInput;
};

/**
 * Creates a new customer.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type CustomerCreate = {
  __typename?: 'CustomerCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  user?: Maybe<User>;
};

/**
 * Event sent when new customer user is created.
 *
 * Added in Saleor 3.2.
 */
export type CustomerCreated = Event & {
  __typename?: 'CustomerCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a customer.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type CustomerDelete = {
  __typename?: 'CustomerDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  user?: Maybe<User>;
};

/** History log of the customer. */
export type CustomerEvent = Node & {
  __typename?: 'CustomerEvent';
  /** App that performed the action. */
  app?: Maybe<App>;
  /** Number of objects concerned by the event. */
  count?: Maybe<Scalars['Int']['output']>;
  /** Date when event happened at in ISO 8601 format. */
  date?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  /** Content of the event. */
  message?: Maybe<Scalars['String']['output']>;
  /** The concerned order. */
  order?: Maybe<Order>;
  /** The concerned order line. */
  orderLine?: Maybe<OrderLine>;
  /** Customer event type. */
  type?: Maybe<CustomerEventsEnum>;
  /** User who performed the action. */
  user?: Maybe<User>;
};

/** An enumeration. */
export enum CustomerEventsEnum {
  AccountActivated = 'ACCOUNT_ACTIVATED',
  AccountCreated = 'ACCOUNT_CREATED',
  AccountDeactivated = 'ACCOUNT_DEACTIVATED',
  CustomerDeleted = 'CUSTOMER_DELETED',
  DigitalLinkDownloaded = 'DIGITAL_LINK_DOWNLOADED',
  EmailAssigned = 'EMAIL_ASSIGNED',
  EmailChanged = 'EMAIL_CHANGED',
  EmailChangedRequest = 'EMAIL_CHANGED_REQUEST',
  NameAssigned = 'NAME_ASSIGNED',
  NoteAdded = 'NOTE_ADDED',
  NoteAddedToOrder = 'NOTE_ADDED_TO_ORDER',
  PasswordChanged = 'PASSWORD_CHANGED',
  PasswordReset = 'PASSWORD_RESET',
  PasswordResetLinkSent = 'PASSWORD_RESET_LINK_SENT',
  PlacedOrder = 'PLACED_ORDER'
}

export type CustomerFilterInput = {
  dateJoined?: InputMaybe<DateRangeInput>;
  /**
   * Filter by ids.
   *
   * Added in Saleor 3.8.
   */
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  numberOfOrders?: InputMaybe<IntRangeInput>;
  placedOrders?: InputMaybe<DateRangeInput>;
  search?: InputMaybe<Scalars['String']['input']>;
  updatedAt?: InputMaybe<DateTimeRangeInput>;
};

export type CustomerInput = {
  /** Billing address of the customer. */
  defaultBillingAddress?: InputMaybe<AddressInput>;
  /** Shipping address of the customer. */
  defaultShippingAddress?: InputMaybe<AddressInput>;
  /** The unique email address of the user. */
  email?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of the customer.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User account is active. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** User language code. */
  languageCode?: InputMaybe<LanguageCodeEnum>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** A note about the user. */
  note?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
};

/**
 * Event sent when customer user metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type CustomerMetadataUpdated = Event & {
  __typename?: 'CustomerMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Updates an existing customer.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type CustomerUpdate = {
  __typename?: 'CustomerUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  user?: Maybe<User>;
};

/**
 * Event sent when customer user is updated.
 *
 * Added in Saleor 3.2.
 */
export type CustomerUpdated = Event & {
  __typename?: 'CustomerUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type DateRangeInput = {
  /** Start date. */
  gte?: InputMaybe<Scalars['Date']['input']>;
  /** End date. */
  lte?: InputMaybe<Scalars['Date']['input']>;
};

export type DateTimeRangeInput = {
  /** Start date. */
  gte?: InputMaybe<Scalars['DateTime']['input']>;
  /** End date. */
  lte?: InputMaybe<Scalars['DateTime']['input']>;
};

/**
 * Deactivate all JWT tokens of the currently authenticated user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type DeactivateAllUserTokens = {
  __typename?: 'DeactivateAllUserTokens';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
};

/** Delete metadata of an object. To use it, you need to have access to the modified object. */
export type DeleteMetadata = {
  __typename?: 'DeleteMetadata';
  errors: Array<MetadataError>;
  item?: Maybe<ObjectWithMetadata>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  metadataErrors: Array<MetadataError>;
};

/** Delete object's private metadata. To use it, you need to be an authenticated staff user or an app and have access to the modified object. */
export type DeletePrivateMetadata = {
  __typename?: 'DeletePrivateMetadata';
  errors: Array<MetadataError>;
  item?: Maybe<ObjectWithMetadata>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  metadataErrors: Array<MetadataError>;
};

/**
 * Represents a delivery method chosen for the checkout. `Warehouse` type is used when checkout is marked as "click and collect" and `ShippingMethod` otherwise.
 *
 * Added in Saleor 3.1.
 */
export type DeliveryMethod = ShippingMethod | Warehouse;

export type DigitalContent = Node & ObjectWithMetadata & {
  __typename?: 'DigitalContent';
  automaticFulfillment: Scalars['Boolean']['output'];
  contentFile: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  maxDownloads?: Maybe<Scalars['Int']['output']>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Product variant assigned to digital content. */
  productVariant: ProductVariant;
  urlValidDays?: Maybe<Scalars['Int']['output']>;
  /** List of URLs for the digital variant. */
  urls?: Maybe<Array<DigitalContentUrl>>;
  useDefaultSettings: Scalars['Boolean']['output'];
};


export type DigitalContentMetafieldArgs = {
  key: Scalars['String']['input'];
};


export type DigitalContentMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


export type DigitalContentPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


export type DigitalContentPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type DigitalContentCountableConnection = {
  __typename?: 'DigitalContentCountableConnection';
  edges: Array<DigitalContentCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DigitalContentCountableEdge = {
  __typename?: 'DigitalContentCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: DigitalContent;
};

/**
 * Create new digital content. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type DigitalContentCreate = {
  __typename?: 'DigitalContentCreate';
  content?: Maybe<DigitalContent>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  variant?: Maybe<ProductVariant>;
};

/**
 * Remove digital content assigned to given variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type DigitalContentDelete = {
  __typename?: 'DigitalContentDelete';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  variant?: Maybe<ProductVariant>;
};

export type DigitalContentInput = {
  /** Overwrite default automatic_fulfillment setting for variant. */
  automaticFulfillment?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines how many times a download link can be accessed by a customer. */
  maxDownloads?: InputMaybe<Scalars['Int']['input']>;
  /**
   * Fields required to update the digital content metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Fields required to update the digital content private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** Determines for how many days a download link is active since it was generated. */
  urlValidDays?: InputMaybe<Scalars['Int']['input']>;
  /** Use default digital content settings for this product. */
  useDefaultSettings: Scalars['Boolean']['input'];
};

/**
 * Update digital content.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type DigitalContentUpdate = {
  __typename?: 'DigitalContentUpdate';
  content?: Maybe<DigitalContent>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  variant?: Maybe<ProductVariant>;
};

export type DigitalContentUploadInput = {
  /** Overwrite default automatic_fulfillment setting for variant. */
  automaticFulfillment?: InputMaybe<Scalars['Boolean']['input']>;
  /** Represents an file in a multipart request. */
  contentFile: Scalars['Upload']['input'];
  /** Determines how many times a download link can be accessed by a customer. */
  maxDownloads?: InputMaybe<Scalars['Int']['input']>;
  /**
   * Fields required to update the digital content metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Fields required to update the digital content private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** Determines for how many days a download link is active since it was generated. */
  urlValidDays?: InputMaybe<Scalars['Int']['input']>;
  /** Use default digital content settings for this product. */
  useDefaultSettings: Scalars['Boolean']['input'];
};

export type DigitalContentUrl = Node & {
  __typename?: 'DigitalContentUrl';
  content: DigitalContent;
  created: Scalars['DateTime']['output'];
  downloadNum: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  /** UUID of digital content. */
  token: Scalars['UUID']['output'];
  /** URL for digital content. */
  url?: Maybe<Scalars['String']['output']>;
};

/**
 * Generate new URL to digital content.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type DigitalContentUrlCreate = {
  __typename?: 'DigitalContentUrlCreate';
  digitalContentUrl?: Maybe<DigitalContentUrl>;
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type DigitalContentUrlCreateInput = {
  /** Digital content ID which URL will belong to. */
  content: Scalars['ID']['input'];
};

export type DiscountError = {
  __typename?: 'DiscountError';
  /** List of channels IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: DiscountErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of products IDs which causes the error. */
  products?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum DiscountErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  CannotManageProductWithoutVariant = 'CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export enum DiscountStatusEnum {
  Active = 'ACTIVE',
  Expired = 'EXPIRED',
  Scheduled = 'SCHEDULED'
}

export enum DiscountValueTypeEnum {
  Fixed = 'FIXED',
  Percentage = 'PERCENTAGE'
}

/** An enumeration. */
export enum DistanceUnitsEnum {
  Cm = 'CM',
  Ft = 'FT',
  Inch = 'INCH',
  Km = 'KM',
  M = 'M',
  Yd = 'YD'
}

/** Represents shop's domain. */
export type Domain = {
  __typename?: 'Domain';
  /** The host name of the domain. */
  host: Scalars['String']['output'];
  /** Inform if SSL is enabled. */
  sslEnabled: Scalars['Boolean']['output'];
  /** Shop's absolute URL. */
  url: Scalars['String']['output'];
};

/**
 * Deletes draft orders.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderBulkDelete = {
  __typename?: 'DraftOrderBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<OrderError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Completes creating an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderComplete = {
  __typename?: 'DraftOrderComplete';
  errors: Array<OrderError>;
  /** Completed order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Creates a new draft order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderCreate = {
  __typename?: 'DraftOrderCreate';
  errors: Array<OrderError>;
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type DraftOrderCreateInput = {
  /** Billing address of the customer. */
  billingAddress?: InputMaybe<AddressInput>;
  /** ID of the channel associated with the order. */
  channelId?: InputMaybe<Scalars['ID']['input']>;
  /** A note from a customer. Visible by customers in the order summary. */
  customerNote?: InputMaybe<Scalars['String']['input']>;
  /** Discount amount for the order. */
  discount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /**
   * External ID of this order.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Variant line input consisting of variant ID and quantity of products. */
  lines?: InputMaybe<Array<OrderLineCreateInput>>;
  /** URL of a view where users should be redirected to see the order details. URL in RFC 1808 format. */
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
  /** Shipping address of the customer. */
  shippingAddress?: InputMaybe<AddressInput>;
  /** ID of a selected shipping method. */
  shippingMethod?: InputMaybe<Scalars['ID']['input']>;
  /** Customer associated with the draft order. */
  user?: InputMaybe<Scalars['ID']['input']>;
  /** Email address of the customer. */
  userEmail?: InputMaybe<Scalars['String']['input']>;
  /** ID of the voucher associated with the order. */
  voucher?: InputMaybe<Scalars['ID']['input']>;
};

/**
 * Event sent when new draft order is created.
 *
 * Added in Saleor 3.2.
 */
export type DraftOrderCreated = Event & {
  __typename?: 'DraftOrderCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a draft order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderDelete = {
  __typename?: 'DraftOrderDelete';
  errors: Array<OrderError>;
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when draft order is deleted.
 *
 * Added in Saleor 3.2.
 */
export type DraftOrderDeleted = Event & {
  __typename?: 'DraftOrderDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type DraftOrderInput = {
  /** Billing address of the customer. */
  billingAddress?: InputMaybe<AddressInput>;
  /** ID of the channel associated with the order. */
  channelId?: InputMaybe<Scalars['ID']['input']>;
  /** A note from a customer. Visible by customers in the order summary. */
  customerNote?: InputMaybe<Scalars['String']['input']>;
  /** Discount amount for the order. */
  discount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /**
   * External ID of this order.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** URL of a view where users should be redirected to see the order details. URL in RFC 1808 format. */
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
  /** Shipping address of the customer. */
  shippingAddress?: InputMaybe<AddressInput>;
  /** ID of a selected shipping method. */
  shippingMethod?: InputMaybe<Scalars['ID']['input']>;
  /** Customer associated with the draft order. */
  user?: InputMaybe<Scalars['ID']['input']>;
  /** Email address of the customer. */
  userEmail?: InputMaybe<Scalars['String']['input']>;
  /** ID of the voucher associated with the order. */
  voucher?: InputMaybe<Scalars['ID']['input']>;
};

/**
 * Deletes order lines.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderLinesBulkDelete = {
  __typename?: 'DraftOrderLinesBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<OrderError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Updates a draft order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type DraftOrderUpdate = {
  __typename?: 'DraftOrderUpdate';
  errors: Array<OrderError>;
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when draft order is updated.
 *
 * Added in Saleor 3.2.
 */
export type DraftOrderUpdated = Event & {
  __typename?: 'DraftOrderUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export enum ErrorPolicyEnum {
  /** Save what is possible within a single row. If there are errors in an input data row, try to save it partially and skip the invalid part. */
  IgnoreFailed = 'IGNORE_FAILED',
  /** Reject all rows if there is at least one error in any of them. */
  RejectEverything = 'REJECT_EVERYTHING',
  /** Reject rows with errors. */
  RejectFailedRows = 'REJECT_FAILED_ROWS'
}

export type Event = {
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Event delivery. */
export type EventDelivery = Node & {
  __typename?: 'EventDelivery';
  /** Event delivery attempts. */
  attempts?: Maybe<EventDeliveryAttemptCountableConnection>;
  createdAt: Scalars['DateTime']['output'];
  /** Webhook event type. */
  eventType: WebhookEventTypeEnum;
  id: Scalars['ID']['output'];
  /** Event payload. */
  payload?: Maybe<Scalars['String']['output']>;
  /** Event delivery status. */
  status: EventDeliveryStatusEnum;
};


/** Event delivery. */
export type EventDeliveryAttemptsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<EventDeliveryAttemptSortingInput>;
};

/** Event delivery attempts. */
export type EventDeliveryAttempt = Node & {
  __typename?: 'EventDeliveryAttempt';
  /** Event delivery creation date and time. */
  createdAt: Scalars['DateTime']['output'];
  /** Delivery attempt duration. */
  duration?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  /** Request headers for delivery attempt. */
  requestHeaders?: Maybe<Scalars['String']['output']>;
  /** Delivery attempt response content. */
  response?: Maybe<Scalars['String']['output']>;
  /** Response headers for delivery attempt. */
  responseHeaders?: Maybe<Scalars['String']['output']>;
  /** Delivery attempt response status code. */
  responseStatusCode?: Maybe<Scalars['Int']['output']>;
  /** Event delivery status. */
  status: EventDeliveryStatusEnum;
  /** Task id for delivery attempt. */
  taskId?: Maybe<Scalars['String']['output']>;
};

export type EventDeliveryAttemptCountableConnection = {
  __typename?: 'EventDeliveryAttemptCountableConnection';
  edges: Array<EventDeliveryAttemptCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type EventDeliveryAttemptCountableEdge = {
  __typename?: 'EventDeliveryAttemptCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: EventDeliveryAttempt;
};

export enum EventDeliveryAttemptSortField {
  /** Sort event delivery attempts by created at. */
  CreatedAt = 'CREATED_AT'
}

export type EventDeliveryAttemptSortingInput = {
  /** Specifies the direction in which to sort attempts. */
  direction: OrderDirection;
  /** Sort attempts by the selected field. */
  field: EventDeliveryAttemptSortField;
};

export type EventDeliveryCountableConnection = {
  __typename?: 'EventDeliveryCountableConnection';
  edges: Array<EventDeliveryCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type EventDeliveryCountableEdge = {
  __typename?: 'EventDeliveryCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: EventDelivery;
};

export type EventDeliveryFilterInput = {
  eventType?: InputMaybe<WebhookEventTypeEnum>;
  status?: InputMaybe<EventDeliveryStatusEnum>;
};

/**
 * Retries event delivery.
 *
 * Requires one of the following permissions: MANAGE_APPS.
 */
export type EventDeliveryRetry = {
  __typename?: 'EventDeliveryRetry';
  /** Event delivery. */
  delivery?: Maybe<EventDelivery>;
  errors: Array<WebhookError>;
};

export enum EventDeliverySortField {
  /** Sort event deliveries by created at. */
  CreatedAt = 'CREATED_AT'
}

export type EventDeliverySortingInput = {
  /** Specifies the direction in which to sort deliveries. */
  direction: OrderDirection;
  /** Sort deliveries by the selected field. */
  field: EventDeliverySortField;
};

export enum EventDeliveryStatusEnum {
  Failed = 'FAILED',
  Pending = 'PENDING',
  Success = 'SUCCESS'
}

export type ExportError = {
  __typename?: 'ExportError';
  /** The error code. */
  code: ExportErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum ExportErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED'
}

/** History log of export file. */
export type ExportEvent = Node & {
  __typename?: 'ExportEvent';
  /** App which performed the action. Requires one of the following permissions: OWNER, MANAGE_APPS. */
  app?: Maybe<App>;
  /** Date when event happened at in ISO 8601 format. */
  date: Scalars['DateTime']['output'];
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /** Content of the event. */
  message: Scalars['String']['output'];
  /** Export event type. */
  type: ExportEventsEnum;
  /** User who performed the action. Requires one of the following permissions: OWNER, MANAGE_STAFF. */
  user?: Maybe<User>;
};

/** An enumeration. */
export enum ExportEventsEnum {
  ExportedFileSent = 'EXPORTED_FILE_SENT',
  ExportDeleted = 'EXPORT_DELETED',
  ExportFailed = 'EXPORT_FAILED',
  ExportFailedInfoSent = 'EXPORT_FAILED_INFO_SENT',
  ExportPending = 'EXPORT_PENDING',
  ExportSuccess = 'EXPORT_SUCCESS'
}

/** Represents a job data of exported file. */
export type ExportFile = Job & Node & {
  __typename?: 'ExportFile';
  app?: Maybe<App>;
  /** Created date time of job in ISO 8601 format. */
  createdAt: Scalars['DateTime']['output'];
  /** List of events associated with the export. */
  events?: Maybe<Array<ExportEvent>>;
  id: Scalars['ID']['output'];
  /** Job message. */
  message?: Maybe<Scalars['String']['output']>;
  /** Job status. */
  status: JobStatusEnum;
  /** Date time of job last update in ISO 8601 format. */
  updatedAt: Scalars['DateTime']['output'];
  /** The URL of field to download. */
  url?: Maybe<Scalars['String']['output']>;
  user?: Maybe<User>;
};

export type ExportFileCountableConnection = {
  __typename?: 'ExportFileCountableConnection';
  edges: Array<ExportFileCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type ExportFileCountableEdge = {
  __typename?: 'ExportFileCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: ExportFile;
};

export type ExportFileFilterInput = {
  app?: InputMaybe<Scalars['String']['input']>;
  createdAt?: InputMaybe<DateTimeRangeInput>;
  status?: InputMaybe<JobStatusEnum>;
  updatedAt?: InputMaybe<DateTimeRangeInput>;
  user?: InputMaybe<Scalars['String']['input']>;
};

export enum ExportFileSortField {
  CreatedAt = 'CREATED_AT',
  LastModifiedAt = 'LAST_MODIFIED_AT',
  Status = 'STATUS',
  UpdatedAt = 'UPDATED_AT'
}

export type ExportFileSortingInput = {
  /** Specifies the direction in which to sort export file. */
  direction: OrderDirection;
  /** Sort export file by the selected field. */
  field: ExportFileSortField;
};

/**
 * Export gift cards to csv file.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type ExportGiftCards = {
  __typename?: 'ExportGiftCards';
  errors: Array<ExportError>;
  /** The newly created export file job which is responsible for export data. */
  exportFile?: Maybe<ExportFile>;
};

export type ExportGiftCardsInput = {
  /** Type of exported file. */
  fileType: FileTypesEnum;
  /** Filtering options for gift cards. */
  filter?: InputMaybe<GiftCardFilterInput>;
  /** List of gift cards IDs to export. */
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Determine which gift cards should be exported. */
  scope: ExportScope;
};

export type ExportInfoInput = {
  /** List of attribute ids witch should be exported. */
  attributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of channels ids which should be exported. */
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of product fields witch should be exported. */
  fields?: InputMaybe<Array<ProductFieldEnum>>;
  /** List of warehouse ids witch should be exported. */
  warehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Export products to csv file.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ExportProducts = {
  __typename?: 'ExportProducts';
  errors: Array<ExportError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  exportErrors: Array<ExportError>;
  /** The newly created export file job which is responsible for export data. */
  exportFile?: Maybe<ExportFile>;
};

export type ExportProductsInput = {
  /** Input with info about fields which should be exported. */
  exportInfo?: InputMaybe<ExportInfoInput>;
  /** Type of exported file. */
  fileType: FileTypesEnum;
  /** Filtering options for products. */
  filter?: InputMaybe<ProductFilterInput>;
  /** List of products IDs to export. */
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Determine which products should be exported. */
  scope: ExportScope;
};

export enum ExportScope {
  /** Export all products. */
  All = 'ALL',
  /** Export the filtered products. */
  Filter = 'FILTER',
  /** Export products with given ids. */
  Ids = 'IDS'
}

export type ExternalAuthentication = {
  __typename?: 'ExternalAuthentication';
  /** ID of external authentication plugin. */
  id: Scalars['String']['output'];
  /** Name of external authentication plugin. */
  name?: Maybe<Scalars['String']['output']>;
};

/** Prepare external authentication URL for user by custom plugin. */
export type ExternalAuthenticationUrl = {
  __typename?: 'ExternalAuthenticationUrl';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** The data returned by authentication plugin. */
  authenticationData?: Maybe<Scalars['JSONString']['output']>;
  errors: Array<AccountError>;
};

/** Logout user by custom plugin. */
export type ExternalLogout = {
  __typename?: 'ExternalLogout';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** The data returned by authentication plugin. */
  logoutData?: Maybe<Scalars['JSONString']['output']>;
};

export type ExternalNotificationError = {
  __typename?: 'ExternalNotificationError';
  /** The error code. */
  code: ExternalNotificationErrorCodes;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum ExternalNotificationErrorCodes {
  ChannelInactive = 'CHANNEL_INACTIVE',
  InvalidModelType = 'INVALID_MODEL_TYPE',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED'
}

/**
 * Trigger sending a notification with the notify plugin method. Serializes nodes provided as ids parameter and includes this data in the notification payload.
 *
 * Added in Saleor 3.1.
 */
export type ExternalNotificationTrigger = {
  __typename?: 'ExternalNotificationTrigger';
  errors: Array<ExternalNotificationError>;
};

export type ExternalNotificationTriggerInput = {
  /** External event type. This field is passed to a plugin as an event type. */
  externalEventType: Scalars['String']['input'];
  /** Additional payload that will be merged with the one based on the bussines object ID. */
  extraPayload?: InputMaybe<Scalars['JSONString']['input']>;
  /** The list of customers or orders node IDs that will be serialized and included in the notification payload. */
  ids: Array<Scalars['ID']['input']>;
};

/** Obtain external access tokens for user by custom plugin. */
export type ExternalObtainAccessTokens = {
  __typename?: 'ExternalObtainAccessTokens';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** CSRF token required to re-generate external access token. */
  csrfToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AccountError>;
  /** The refresh token, required to re-generate external access token. */
  refreshToken?: Maybe<Scalars['String']['output']>;
  /** The token, required to authenticate. */
  token?: Maybe<Scalars['String']['output']>;
  /** A user instance. */
  user?: Maybe<User>;
};

/** Refresh user's access by custom plugin. */
export type ExternalRefresh = {
  __typename?: 'ExternalRefresh';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** CSRF token required to re-generate external access token. */
  csrfToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AccountError>;
  /** The refresh token, required to re-generate external access token. */
  refreshToken?: Maybe<Scalars['String']['output']>;
  /** The token, required to authenticate. */
  token?: Maybe<Scalars['String']['output']>;
  /** A user instance. */
  user?: Maybe<User>;
};

/** Verify external authentication data by plugin. */
export type ExternalVerify = {
  __typename?: 'ExternalVerify';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** Determine if authentication data is valid or not. */
  isValid: Scalars['Boolean']['output'];
  /** User assigned to data. */
  user?: Maybe<User>;
  /** External data. */
  verifyData?: Maybe<Scalars['JSONString']['output']>;
};

export type File = {
  __typename?: 'File';
  /** Content type of the file. */
  contentType?: Maybe<Scalars['String']['output']>;
  /** The URL of the file. */
  url: Scalars['String']['output'];
};

/** An enumeration. */
export enum FileTypesEnum {
  Csv = 'CSV',
  Xlsx = 'XLSX'
}

/**
 * Upload a file. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
 *
 * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
 */
export type FileUpload = {
  __typename?: 'FileUpload';
  errors: Array<UploadError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  uploadErrors: Array<UploadError>;
  uploadedFile?: Maybe<File>;
};

/** Represents order fulfillment. */
export type Fulfillment = Node & ObjectWithMetadata & {
  __typename?: 'Fulfillment';
  created: Scalars['DateTime']['output'];
  fulfillmentOrder: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  /** List of lines for the fulfillment. */
  lines?: Maybe<Array<FulfillmentLine>>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  status: FulfillmentStatus;
  /** User-friendly fulfillment status. */
  statusDisplay?: Maybe<Scalars['String']['output']>;
  trackingNumber: Scalars['String']['output'];
  /** Warehouse from fulfillment was fulfilled. */
  warehouse?: Maybe<Warehouse>;
};


/** Represents order fulfillment. */
export type FulfillmentMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents order fulfillment. */
export type FulfillmentMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents order fulfillment. */
export type FulfillmentPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents order fulfillment. */
export type FulfillmentPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Approve existing fulfillment.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type FulfillmentApprove = {
  __typename?: 'FulfillmentApprove';
  errors: Array<OrderError>;
  /** An approved fulfillment. */
  fulfillment?: Maybe<Fulfillment>;
  /** Order which fulfillment was approved. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when fulfillment is approved.
 *
 * Added in Saleor 3.7.
 */
export type FulfillmentApproved = Event & {
  __typename?: 'FulfillmentApproved';
  /** The fulfillment the event relates to. */
  fulfillment?: Maybe<Fulfillment>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the fulfillment belongs to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Cancels existing fulfillment and optionally restocks items.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type FulfillmentCancel = {
  __typename?: 'FulfillmentCancel';
  errors: Array<OrderError>;
  /** A canceled fulfillment. */
  fulfillment?: Maybe<Fulfillment>;
  /** Order which fulfillment was cancelled. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type FulfillmentCancelInput = {
  /** ID of a warehouse where items will be restocked. Optional when fulfillment is in WAITING_FOR_APPROVAL state. */
  warehouseId?: InputMaybe<Scalars['ID']['input']>;
};

/**
 * Event sent when fulfillment is canceled.
 *
 * Added in Saleor 3.4.
 */
export type FulfillmentCanceled = Event & {
  __typename?: 'FulfillmentCanceled';
  /** The fulfillment the event relates to. */
  fulfillment?: Maybe<Fulfillment>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the fulfillment belongs to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when new fulfillment is created.
 *
 * Added in Saleor 3.4.
 */
export type FulfillmentCreated = Event & {
  __typename?: 'FulfillmentCreated';
  /** The fulfillment the event relates to. */
  fulfillment?: Maybe<Fulfillment>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the fulfillment belongs to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents line of the fulfillment. */
export type FulfillmentLine = Node & {
  __typename?: 'FulfillmentLine';
  id: Scalars['ID']['output'];
  orderLine?: Maybe<OrderLine>;
  quantity: Scalars['Int']['output'];
};

/**
 * Event sent when fulfillment metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type FulfillmentMetadataUpdated = Event & {
  __typename?: 'FulfillmentMetadataUpdated';
  /** The fulfillment the event relates to. */
  fulfillment?: Maybe<Fulfillment>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the fulfillment belongs to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Refund products.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type FulfillmentRefundProducts = {
  __typename?: 'FulfillmentRefundProducts';
  errors: Array<OrderError>;
  /** A refunded fulfillment. */
  fulfillment?: Maybe<Fulfillment>;
  /** Order which fulfillment was refunded. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Return products.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type FulfillmentReturnProducts = {
  __typename?: 'FulfillmentReturnProducts';
  errors: Array<OrderError>;
  /** Order which fulfillment was returned. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  /** A replace fulfillment. */
  replaceFulfillment?: Maybe<Fulfillment>;
  /** A draft order which was created for products with replace flag. */
  replaceOrder?: Maybe<Order>;
  /** A return fulfillment. */
  returnFulfillment?: Maybe<Fulfillment>;
};

/** An enumeration. */
export enum FulfillmentStatus {
  Canceled = 'CANCELED',
  Fulfilled = 'FULFILLED',
  Refunded = 'REFUNDED',
  RefundedAndReturned = 'REFUNDED_AND_RETURNED',
  Replaced = 'REPLACED',
  Returned = 'RETURNED',
  WaitingForApproval = 'WAITING_FOR_APPROVAL'
}

/**
 * Updates a fulfillment for an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type FulfillmentUpdateTracking = {
  __typename?: 'FulfillmentUpdateTracking';
  errors: Array<OrderError>;
  /** A fulfillment with updated tracking. */
  fulfillment?: Maybe<Fulfillment>;
  /** Order for which fulfillment was updated. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type FulfillmentUpdateTrackingInput = {
  /** If true, send an email notification to the customer. */
  notifyCustomer?: InputMaybe<Scalars['Boolean']['input']>;
  /** Fulfillment tracking number. */
  trackingNumber?: InputMaybe<Scalars['String']['input']>;
};

/** Payment gateway client configuration key and value pair. */
export type GatewayConfigLine = {
  __typename?: 'GatewayConfigLine';
  /** Gateway config key. */
  field: Scalars['String']['output'];
  /** Gateway config value for key. */
  value?: Maybe<Scalars['String']['output']>;
};

/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCard = Node & ObjectWithMetadata & {
  __typename?: 'GiftCard';
  /**
   * App which created the gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_APPS, OWNER.
   */
  app?: Maybe<App>;
  /**
   * Slug of the channel where the gift card was bought.
   *
   * Added in Saleor 3.1.
   */
  boughtInChannel?: Maybe<Scalars['String']['output']>;
  /** Gift card code. Can be fetched by a staff member with MANAGE_GIFT_CARD when gift card wasn't yet used and by the gift card owner. */
  code: Scalars['String']['output'];
  created: Scalars['DateTime']['output'];
  /**
   * The user who bought or issued a gift card.
   *
   * Added in Saleor 3.1.
   */
  createdBy?: Maybe<User>;
  /**
   * Email address of the user who bought or issued gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_USERS, OWNER.
   */
  createdByEmail?: Maybe<Scalars['String']['output']>;
  currentBalance: Money;
  /** Code in format which allows displaying in a user interface. */
  displayCode: Scalars['String']['output'];
  /**
   * End date of gift card.
   * @deprecated This field will be removed in Saleor 4.0. Use `expiryDate` field instead.
   */
  endDate?: Maybe<Scalars['DateTime']['output']>;
  /**
   * List of events associated with the gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  events: Array<GiftCardEvent>;
  expiryDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['ID']['output'];
  initialBalance: Money;
  isActive: Scalars['Boolean']['output'];
  /** Last 4 characters of gift card code. */
  last4CodeChars: Scalars['String']['output'];
  lastUsedOn?: Maybe<Scalars['DateTime']['output']>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * Related gift card product.
   *
   * Added in Saleor 3.1.
   */
  product?: Maybe<Product>;
  /**
   * Start date of gift card.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  startDate?: Maybe<Scalars['DateTime']['output']>;
  /**
   * The gift card tag.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  tags: Array<GiftCardTag>;
  /**
   * The customer who used a gift card.
   *
   * Added in Saleor 3.1.
   */
  usedBy?: Maybe<User>;
  /**
   * Email address of the customer who used a gift card.
   *
   * Added in Saleor 3.1.
   */
  usedByEmail?: Maybe<Scalars['String']['output']>;
  /**
   * The customer who bought a gift card.
   * @deprecated This field will be removed in Saleor 4.0. Use `createdBy` field instead.
   */
  user?: Maybe<User>;
};


/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCardEventsArgs = {
  filter?: InputMaybe<GiftCardEventFilterInput>;
};


/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCardMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCardMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCardPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** A gift card is a prepaid electronic payment card accepted in stores. They can be used during checkout by providing a valid gift card codes. */
export type GiftCardPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Activate a gift card.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardActivate = {
  __typename?: 'GiftCardActivate';
  errors: Array<GiftCardError>;
  /** Activated gift card. */
  giftCard?: Maybe<GiftCard>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  giftCardErrors: Array<GiftCardError>;
};

/**
 * Adds note to the gift card.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardAddNote = {
  __typename?: 'GiftCardAddNote';
  errors: Array<GiftCardError>;
  /** Gift card note created. */
  event?: Maybe<GiftCardEvent>;
  /** Gift card with the note added. */
  giftCard?: Maybe<GiftCard>;
};

export type GiftCardAddNoteInput = {
  /** Note message. */
  message: Scalars['String']['input'];
};

/**
 * Activate gift cards.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardBulkActivate = {
  __typename?: 'GiftCardBulkActivate';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<GiftCardError>;
};

/**
 * Create gift cards.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardBulkCreate = {
  __typename?: 'GiftCardBulkCreate';
  /** Returns how many objects were created. */
  count: Scalars['Int']['output'];
  errors: Array<GiftCardError>;
  /** List of created gift cards. */
  giftCards: Array<GiftCard>;
};

export type GiftCardBulkCreateInput = {
  /** Balance of the gift card. */
  balance: PriceInput;
  /** The number of cards to issue. */
  count: Scalars['Int']['input'];
  /** The gift card expiry date. */
  expiryDate?: InputMaybe<Scalars['Date']['input']>;
  /** Determine if gift card is active. */
  isActive: Scalars['Boolean']['input'];
  /** The gift card tags. */
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Deactivate gift cards.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardBulkDeactivate = {
  __typename?: 'GiftCardBulkDeactivate';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<GiftCardError>;
};

/**
 * Delete gift cards.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardBulkDelete = {
  __typename?: 'GiftCardBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<GiftCardError>;
};

export type GiftCardCountableConnection = {
  __typename?: 'GiftCardCountableConnection';
  edges: Array<GiftCardCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type GiftCardCountableEdge = {
  __typename?: 'GiftCardCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: GiftCard;
};

/**
 * Creates a new gift card.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardCreate = {
  __typename?: 'GiftCardCreate';
  errors: Array<GiftCardError>;
  giftCard?: Maybe<GiftCard>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  giftCardErrors: Array<GiftCardError>;
};

export type GiftCardCreateInput = {
  /**
   * The gift card tags to add.
   *
   * Added in Saleor 3.1.
   */
  addTags?: InputMaybe<Array<Scalars['String']['input']>>;
  /** Balance of the gift card. */
  balance: PriceInput;
  /**
   * Slug of a channel from which the email should be sent.
   *
   * Added in Saleor 3.1.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /**
   * Code to use the gift card.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. The code is now auto generated.
   */
  code?: InputMaybe<Scalars['String']['input']>;
  /**
   * End date of the gift card in ISO 8601 format.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `expiryDate` from `expirySettings` instead.
   */
  endDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * The gift card expiry date.
   *
   * Added in Saleor 3.1.
   */
  expiryDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * Determine if gift card is active.
   *
   * Added in Saleor 3.1.
   */
  isActive: Scalars['Boolean']['input'];
  /**
   * The gift card note from the staff member.
   *
   * Added in Saleor 3.1.
   */
  note?: InputMaybe<Scalars['String']['input']>;
  /**
   * Start date of the gift card in ISO 8601 format.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  startDate?: InputMaybe<Scalars['Date']['input']>;
  /** Email of the customer to whom gift card will be sent. */
  userEmail?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new gift card is created.
 *
 * Added in Saleor 3.2.
 */
export type GiftCardCreated = Event & {
  __typename?: 'GiftCardCreated';
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deactivate a gift card.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardDeactivate = {
  __typename?: 'GiftCardDeactivate';
  errors: Array<GiftCardError>;
  /** Deactivated gift card. */
  giftCard?: Maybe<GiftCard>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  giftCardErrors: Array<GiftCardError>;
};

/**
 * Delete gift card.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardDelete = {
  __typename?: 'GiftCardDelete';
  errors: Array<GiftCardError>;
  giftCard?: Maybe<GiftCard>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  giftCardErrors: Array<GiftCardError>;
};

/**
 * Event sent when gift card is deleted.
 *
 * Added in Saleor 3.2.
 */
export type GiftCardDeleted = Event & {
  __typename?: 'GiftCardDeleted';
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type GiftCardError = {
  __typename?: 'GiftCardError';
  /** The error code. */
  code: GiftCardErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of tag values that cause the error. */
  tags?: Maybe<Array<Scalars['String']['output']>>;
};

/** An enumeration. */
export enum GiftCardErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  ExpiredGiftCard = 'EXPIRED_GIFT_CARD',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

/**
 * History log of the gift card.
 *
 * Added in Saleor 3.1.
 */
export type GiftCardEvent = Node & {
  __typename?: 'GiftCardEvent';
  /** App that performed the action. Requires one of the following permissions: MANAGE_APPS, OWNER. */
  app?: Maybe<App>;
  /** The gift card balance. */
  balance?: Maybe<GiftCardEventBalance>;
  /** Date when event happened at in ISO 8601 format. */
  date?: Maybe<Scalars['DateTime']['output']>;
  /** Email of the customer. */
  email?: Maybe<Scalars['String']['output']>;
  /** The gift card expiry date. */
  expiryDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['ID']['output'];
  /** Content of the event. */
  message?: Maybe<Scalars['String']['output']>;
  /** Previous gift card expiry date. */
  oldExpiryDate?: Maybe<Scalars['Date']['output']>;
  /** The list of old gift card tags. */
  oldTags?: Maybe<Array<Scalars['String']['output']>>;
  /** The order ID where gift card was used or bought. */
  orderId?: Maybe<Scalars['ID']['output']>;
  /** User-friendly number of an order where gift card was used or bought. */
  orderNumber?: Maybe<Scalars['String']['output']>;
  /** The list of gift card tags. */
  tags?: Maybe<Array<Scalars['String']['output']>>;
  /** Gift card event type. */
  type?: Maybe<GiftCardEventsEnum>;
  /** User who performed the action. Requires one of the following permissions: MANAGE_USERS, MANAGE_STAFF, OWNER. */
  user?: Maybe<User>;
};

export type GiftCardEventBalance = {
  __typename?: 'GiftCardEventBalance';
  /** Current balance of the gift card. */
  currentBalance: Money;
  /** Initial balance of the gift card. */
  initialBalance?: Maybe<Money>;
  /** Previous current balance of the gift card. */
  oldCurrentBalance?: Maybe<Money>;
  /** Previous initial balance of the gift card. */
  oldInitialBalance?: Maybe<Money>;
};

export type GiftCardEventFilterInput = {
  orders?: InputMaybe<Array<Scalars['ID']['input']>>;
  type?: InputMaybe<GiftCardEventsEnum>;
};

/** An enumeration. */
export enum GiftCardEventsEnum {
  Activated = 'ACTIVATED',
  BalanceReset = 'BALANCE_RESET',
  Bought = 'BOUGHT',
  Deactivated = 'DEACTIVATED',
  ExpiryDateUpdated = 'EXPIRY_DATE_UPDATED',
  Issued = 'ISSUED',
  NoteAdded = 'NOTE_ADDED',
  Resent = 'RESENT',
  SentToCustomer = 'SENT_TO_CUSTOMER',
  TagsUpdated = 'TAGS_UPDATED',
  Updated = 'UPDATED',
  UsedInOrder = 'USED_IN_ORDER'
}

export type GiftCardFilterInput = {
  code?: InputMaybe<Scalars['String']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
  currentBalance?: InputMaybe<PriceRangeInput>;
  initialBalance?: InputMaybe<PriceRangeInput>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  products?: InputMaybe<Array<Scalars['ID']['input']>>;
  tags?: InputMaybe<Array<Scalars['String']['input']>>;
  used?: InputMaybe<Scalars['Boolean']['input']>;
  usedBy?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Event sent when gift card metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type GiftCardMetadataUpdated = Event & {
  __typename?: 'GiftCardMetadataUpdated';
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Resend a gift card.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardResend = {
  __typename?: 'GiftCardResend';
  errors: Array<GiftCardError>;
  /** Gift card which has been sent. */
  giftCard?: Maybe<GiftCard>;
};

export type GiftCardResendInput = {
  /** Slug of a channel from which the email should be sent. */
  channel: Scalars['String']['input'];
  /** Email to which gift card should be send. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** ID of a gift card to resend. */
  id: Scalars['ID']['input'];
};

/**
 * Event sent when gift card is e-mailed.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type GiftCardSent = Event & {
  __typename?: 'GiftCardSent';
  /** Slug of a channel for which this gift card email was sent. */
  channel?: Maybe<Scalars['String']['output']>;
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** E-mail address to which gift card was sent. */
  sentToEmail?: Maybe<Scalars['String']['output']>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Gift card related settings from site settings. */
export type GiftCardSettings = {
  __typename?: 'GiftCardSettings';
  /** The gift card expiry period settings. */
  expiryPeriod?: Maybe<TimePeriod>;
  /** The gift card expiry type settings. */
  expiryType: GiftCardSettingsExpiryTypeEnum;
};

export type GiftCardSettingsError = {
  __typename?: 'GiftCardSettingsError';
  /** The error code. */
  code: GiftCardSettingsErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum GiftCardSettingsErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  Required = 'REQUIRED'
}

/** An enumeration. */
export enum GiftCardSettingsExpiryTypeEnum {
  ExpiryPeriod = 'EXPIRY_PERIOD',
  NeverExpire = 'NEVER_EXPIRE'
}

/**
 * Update gift card settings.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardSettingsUpdate = {
  __typename?: 'GiftCardSettingsUpdate';
  errors: Array<GiftCardSettingsError>;
  /** Gift card settings. */
  giftCardSettings?: Maybe<GiftCardSettings>;
};

export type GiftCardSettingsUpdateInput = {
  /** Defines gift card expiry period. */
  expiryPeriod?: InputMaybe<TimePeriodInputType>;
  /** Defines gift card default expiry settings. */
  expiryType?: InputMaybe<GiftCardSettingsExpiryTypeEnum>;
};

export enum GiftCardSortField {
  /**
   * Sort gift cards by created at.
   *
   * Added in Saleor 3.8.
   */
  CreatedAt = 'CREATED_AT',
  /** Sort gift cards by current balance. */
  CurrentBalance = 'CURRENT_BALANCE',
  /** Sort gift cards by product. */
  Product = 'PRODUCT',
  /** Sort gift cards by used by. */
  UsedBy = 'USED_BY'
}

export type GiftCardSortingInput = {
  /** Specifies the direction in which to sort gift cards. */
  direction: OrderDirection;
  /** Sort gift cards by the selected field. */
  field: GiftCardSortField;
};

/**
 * Event sent when gift card status has changed.
 *
 * Added in Saleor 3.2.
 */
export type GiftCardStatusChanged = Event & {
  __typename?: 'GiftCardStatusChanged';
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * The gift card tag.
 *
 * Added in Saleor 3.1.
 */
export type GiftCardTag = Node & {
  __typename?: 'GiftCardTag';
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
};

export type GiftCardTagCountableConnection = {
  __typename?: 'GiftCardTagCountableConnection';
  edges: Array<GiftCardTagCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type GiftCardTagCountableEdge = {
  __typename?: 'GiftCardTagCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: GiftCardTag;
};

export type GiftCardTagFilterInput = {
  search?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Update a gift card.
 *
 * Requires one of the following permissions: MANAGE_GIFT_CARD.
 */
export type GiftCardUpdate = {
  __typename?: 'GiftCardUpdate';
  errors: Array<GiftCardError>;
  giftCard?: Maybe<GiftCard>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  giftCardErrors: Array<GiftCardError>;
};

export type GiftCardUpdateInput = {
  /**
   * The gift card tags to add.
   *
   * Added in Saleor 3.1.
   */
  addTags?: InputMaybe<Array<Scalars['String']['input']>>;
  /**
   * The gift card balance amount.
   *
   * Added in Saleor 3.1.
   */
  balanceAmount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /**
   * End date of the gift card in ISO 8601 format.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `expiryDate` from `expirySettings` instead.
   */
  endDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * The gift card expiry date.
   *
   * Added in Saleor 3.1.
   */
  expiryDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * The gift card tags to remove.
   *
   * Added in Saleor 3.1.
   */
  removeTags?: InputMaybe<Array<Scalars['String']['input']>>;
  /**
   * Start date of the gift card in ISO 8601 format.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  startDate?: InputMaybe<Scalars['Date']['input']>;
};

/**
 * Event sent when gift card is updated.
 *
 * Added in Saleor 3.2.
 */
export type GiftCardUpdated = Event & {
  __typename?: 'GiftCardUpdated';
  /** The gift card the event relates to. */
  giftCard?: Maybe<GiftCard>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents permission group data. */
export type Group = Node & {
  __typename?: 'Group';
  /**
   * List of channels the group has access to.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  accessibleChannels?: Maybe<Array<Channel>>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /** List of group permissions */
  permissions?: Maybe<Array<Permission>>;
  /**
   * Determine if the group have restricted access to channels.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  restrictedAccessToChannels: Scalars['Boolean']['output'];
  /** True, if the currently authenticated user has rights to manage a group. */
  userCanManage: Scalars['Boolean']['output'];
  /**
   * List of group users
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  users?: Maybe<Array<User>>;
};

export type GroupCountableConnection = {
  __typename?: 'GroupCountableConnection';
  edges: Array<GroupCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type GroupCountableEdge = {
  __typename?: 'GroupCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Group;
};

/** Represents an image. */
export type Image = {
  __typename?: 'Image';
  /** Alt text for an image. */
  alt?: Maybe<Scalars['String']['output']>;
  /** The URL of the image. */
  url: Scalars['String']['output'];
};

export type IntRangeInput = {
  /** Value greater than or equal to. */
  gte?: InputMaybe<Scalars['Int']['input']>;
  /** Value less than or equal to. */
  lte?: InputMaybe<Scalars['Int']['input']>;
};

/** Represents an Invoice. */
export type Invoice = Job & Node & ObjectWithMetadata & {
  __typename?: 'Invoice';
  createdAt: Scalars['DateTime']['output'];
  externalUrl?: Maybe<Scalars['String']['output']>;
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  message?: Maybe<Scalars['String']['output']>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  number?: Maybe<Scalars['String']['output']>;
  /**
   * Order related to the invoice.
   *
   * Added in Saleor 3.10.
   */
  order?: Maybe<Order>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Job status. */
  status: JobStatusEnum;
  updatedAt: Scalars['DateTime']['output'];
  /** URL to download an invoice. */
  url?: Maybe<Scalars['String']['output']>;
};


/** Represents an Invoice. */
export type InvoiceMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an Invoice. */
export type InvoiceMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents an Invoice. */
export type InvoicePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an Invoice. */
export type InvoicePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Creates a ready to send invoice.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceCreate = {
  __typename?: 'InvoiceCreate';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
};

export type InvoiceCreateInput = {
  /**
   * Fields required to update the invoice metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Invoice number. */
  number: Scalars['String']['input'];
  /**
   * Fields required to update the invoice private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** URL of an invoice to download. */
  url: Scalars['String']['input'];
};

/**
 * Deletes an invoice.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceDelete = {
  __typename?: 'InvoiceDelete';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
};

/**
 * Event sent when invoice is deleted.
 *
 * Added in Saleor 3.2.
 */
export type InvoiceDeleted = Event & {
  __typename?: 'InvoiceDeleted';
  /** The invoice the event relates to. */
  invoice?: Maybe<Invoice>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /**
   * Order related to the invoice.
   *
   * Added in Saleor 3.10.
   */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type InvoiceError = {
  __typename?: 'InvoiceError';
  /** The error code. */
  code: InvoiceErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum InvoiceErrorCode {
  EmailNotSet = 'EMAIL_NOT_SET',
  InvalidStatus = 'INVALID_STATUS',
  NotFound = 'NOT_FOUND',
  NotReady = 'NOT_READY',
  NoInvoicePlugin = 'NO_INVOICE_PLUGIN',
  NumberNotSet = 'NUMBER_NOT_SET',
  Required = 'REQUIRED',
  UrlNotSet = 'URL_NOT_SET'
}

/**
 * Request an invoice for the order using plugin.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceRequest = {
  __typename?: 'InvoiceRequest';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
  /** Order related to an invoice. */
  order?: Maybe<Order>;
};

/**
 * Requests deletion of an invoice.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceRequestDelete = {
  __typename?: 'InvoiceRequestDelete';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
};

/**
 * Event sent when invoice is requested.
 *
 * Added in Saleor 3.2.
 */
export type InvoiceRequested = Event & {
  __typename?: 'InvoiceRequested';
  /** The invoice the event relates to. */
  invoice?: Maybe<Invoice>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /**
   * Order related to the invoice.
   *
   * Added in Saleor 3.10.
   */
  order: Order;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Send an invoice notification to the customer.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceSendNotification = {
  __typename?: 'InvoiceSendNotification';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
};

/**
 * Event sent when invoice is sent.
 *
 * Added in Saleor 3.2.
 */
export type InvoiceSent = Event & {
  __typename?: 'InvoiceSent';
  /** The invoice the event relates to. */
  invoice?: Maybe<Invoice>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /**
   * Order related to the invoice.
   *
   * Added in Saleor 3.10.
   */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Updates an invoice.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type InvoiceUpdate = {
  __typename?: 'InvoiceUpdate';
  errors: Array<InvoiceError>;
  invoice?: Maybe<Invoice>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  invoiceErrors: Array<InvoiceError>;
};

export type IssuingPrincipal = App | User;

export type Job = {
  /** Created date time of job in ISO 8601 format. */
  createdAt: Scalars['DateTime']['output'];
  /** Job message. */
  message?: Maybe<Scalars['String']['output']>;
  /** Job status. */
  status: JobStatusEnum;
  /** Date time of job last update in ISO 8601 format. */
  updatedAt: Scalars['DateTime']['output'];
};

/** An enumeration. */
export enum JobStatusEnum {
  Deleted = 'DELETED',
  Failed = 'FAILED',
  Pending = 'PENDING',
  Success = 'SUCCESS'
}

/** An enumeration. */
export enum LanguageCodeEnum {
  Af = 'AF',
  AfNa = 'AF_NA',
  AfZa = 'AF_ZA',
  Agq = 'AGQ',
  AgqCm = 'AGQ_CM',
  Ak = 'AK',
  AkGh = 'AK_GH',
  Am = 'AM',
  AmEt = 'AM_ET',
  Ar = 'AR',
  ArAe = 'AR_AE',
  ArBh = 'AR_BH',
  ArDj = 'AR_DJ',
  ArDz = 'AR_DZ',
  ArEg = 'AR_EG',
  ArEh = 'AR_EH',
  ArEr = 'AR_ER',
  ArIl = 'AR_IL',
  ArIq = 'AR_IQ',
  ArJo = 'AR_JO',
  ArKm = 'AR_KM',
  ArKw = 'AR_KW',
  ArLb = 'AR_LB',
  ArLy = 'AR_LY',
  ArMa = 'AR_MA',
  ArMr = 'AR_MR',
  ArOm = 'AR_OM',
  ArPs = 'AR_PS',
  ArQa = 'AR_QA',
  ArSa = 'AR_SA',
  ArSd = 'AR_SD',
  ArSo = 'AR_SO',
  ArSs = 'AR_SS',
  ArSy = 'AR_SY',
  ArTd = 'AR_TD',
  ArTn = 'AR_TN',
  ArYe = 'AR_YE',
  As = 'AS',
  Asa = 'ASA',
  AsaTz = 'ASA_TZ',
  Ast = 'AST',
  AstEs = 'AST_ES',
  AsIn = 'AS_IN',
  Az = 'AZ',
  AzCyrl = 'AZ_CYRL',
  AzCyrlAz = 'AZ_CYRL_AZ',
  AzLatn = 'AZ_LATN',
  AzLatnAz = 'AZ_LATN_AZ',
  Bas = 'BAS',
  BasCm = 'BAS_CM',
  Be = 'BE',
  Bem = 'BEM',
  BemZm = 'BEM_ZM',
  Bez = 'BEZ',
  BezTz = 'BEZ_TZ',
  BeBy = 'BE_BY',
  Bg = 'BG',
  BgBg = 'BG_BG',
  Bm = 'BM',
  BmMl = 'BM_ML',
  Bn = 'BN',
  BnBd = 'BN_BD',
  BnIn = 'BN_IN',
  Bo = 'BO',
  BoCn = 'BO_CN',
  BoIn = 'BO_IN',
  Br = 'BR',
  Brx = 'BRX',
  BrxIn = 'BRX_IN',
  BrFr = 'BR_FR',
  Bs = 'BS',
  BsCyrl = 'BS_CYRL',
  BsCyrlBa = 'BS_CYRL_BA',
  BsLatn = 'BS_LATN',
  BsLatnBa = 'BS_LATN_BA',
  Ca = 'CA',
  CaAd = 'CA_AD',
  CaEs = 'CA_ES',
  CaEsValencia = 'CA_ES_VALENCIA',
  CaFr = 'CA_FR',
  CaIt = 'CA_IT',
  Ccp = 'CCP',
  CcpBd = 'CCP_BD',
  CcpIn = 'CCP_IN',
  Ce = 'CE',
  Ceb = 'CEB',
  CebPh = 'CEB_PH',
  CeRu = 'CE_RU',
  Cgg = 'CGG',
  CggUg = 'CGG_UG',
  Chr = 'CHR',
  ChrUs = 'CHR_US',
  Ckb = 'CKB',
  CkbIq = 'CKB_IQ',
  CkbIr = 'CKB_IR',
  Cs = 'CS',
  CsCz = 'CS_CZ',
  Cu = 'CU',
  CuRu = 'CU_RU',
  Cy = 'CY',
  CyGb = 'CY_GB',
  Da = 'DA',
  Dav = 'DAV',
  DavKe = 'DAV_KE',
  DaDk = 'DA_DK',
  DaGl = 'DA_GL',
  De = 'DE',
  DeAt = 'DE_AT',
  DeBe = 'DE_BE',
  DeCh = 'DE_CH',
  DeDe = 'DE_DE',
  DeIt = 'DE_IT',
  DeLi = 'DE_LI',
  DeLu = 'DE_LU',
  Dje = 'DJE',
  DjeNe = 'DJE_NE',
  Dsb = 'DSB',
  DsbDe = 'DSB_DE',
  Dua = 'DUA',
  DuaCm = 'DUA_CM',
  Dyo = 'DYO',
  DyoSn = 'DYO_SN',
  Dz = 'DZ',
  DzBt = 'DZ_BT',
  Ebu = 'EBU',
  EbuKe = 'EBU_KE',
  Ee = 'EE',
  EeGh = 'EE_GH',
  EeTg = 'EE_TG',
  El = 'EL',
  ElCy = 'EL_CY',
  ElGr = 'EL_GR',
  En = 'EN',
  EnAe = 'EN_AE',
  EnAg = 'EN_AG',
  EnAi = 'EN_AI',
  EnAs = 'EN_AS',
  EnAt = 'EN_AT',
  EnAu = 'EN_AU',
  EnBb = 'EN_BB',
  EnBe = 'EN_BE',
  EnBi = 'EN_BI',
  EnBm = 'EN_BM',
  EnBs = 'EN_BS',
  EnBw = 'EN_BW',
  EnBz = 'EN_BZ',
  EnCa = 'EN_CA',
  EnCc = 'EN_CC',
  EnCh = 'EN_CH',
  EnCk = 'EN_CK',
  EnCm = 'EN_CM',
  EnCx = 'EN_CX',
  EnCy = 'EN_CY',
  EnDe = 'EN_DE',
  EnDg = 'EN_DG',
  EnDk = 'EN_DK',
  EnDm = 'EN_DM',
  EnEr = 'EN_ER',
  EnFi = 'EN_FI',
  EnFj = 'EN_FJ',
  EnFk = 'EN_FK',
  EnFm = 'EN_FM',
  EnGb = 'EN_GB',
  EnGd = 'EN_GD',
  EnGg = 'EN_GG',
  EnGh = 'EN_GH',
  EnGi = 'EN_GI',
  EnGm = 'EN_GM',
  EnGu = 'EN_GU',
  EnGy = 'EN_GY',
  EnHk = 'EN_HK',
  EnIe = 'EN_IE',
  EnIl = 'EN_IL',
  EnIm = 'EN_IM',
  EnIn = 'EN_IN',
  EnIo = 'EN_IO',
  EnJe = 'EN_JE',
  EnJm = 'EN_JM',
  EnKe = 'EN_KE',
  EnKi = 'EN_KI',
  EnKn = 'EN_KN',
  EnKy = 'EN_KY',
  EnLc = 'EN_LC',
  EnLr = 'EN_LR',
  EnLs = 'EN_LS',
  EnMg = 'EN_MG',
  EnMh = 'EN_MH',
  EnMo = 'EN_MO',
  EnMp = 'EN_MP',
  EnMs = 'EN_MS',
  EnMt = 'EN_MT',
  EnMu = 'EN_MU',
  EnMw = 'EN_MW',
  EnMy = 'EN_MY',
  EnNa = 'EN_NA',
  EnNf = 'EN_NF',
  EnNg = 'EN_NG',
  EnNl = 'EN_NL',
  EnNr = 'EN_NR',
  EnNu = 'EN_NU',
  EnNz = 'EN_NZ',
  EnPg = 'EN_PG',
  EnPh = 'EN_PH',
  EnPk = 'EN_PK',
  EnPn = 'EN_PN',
  EnPr = 'EN_PR',
  EnPw = 'EN_PW',
  EnRw = 'EN_RW',
  EnSb = 'EN_SB',
  EnSc = 'EN_SC',
  EnSd = 'EN_SD',
  EnSe = 'EN_SE',
  EnSg = 'EN_SG',
  EnSh = 'EN_SH',
  EnSi = 'EN_SI',
  EnSl = 'EN_SL',
  EnSs = 'EN_SS',
  EnSx = 'EN_SX',
  EnSz = 'EN_SZ',
  EnTc = 'EN_TC',
  EnTk = 'EN_TK',
  EnTo = 'EN_TO',
  EnTt = 'EN_TT',
  EnTv = 'EN_TV',
  EnTz = 'EN_TZ',
  EnUg = 'EN_UG',
  EnUm = 'EN_UM',
  EnUs = 'EN_US',
  EnVc = 'EN_VC',
  EnVg = 'EN_VG',
  EnVi = 'EN_VI',
  EnVu = 'EN_VU',
  EnWs = 'EN_WS',
  EnZa = 'EN_ZA',
  EnZm = 'EN_ZM',
  EnZw = 'EN_ZW',
  Eo = 'EO',
  Es = 'ES',
  EsAr = 'ES_AR',
  EsBo = 'ES_BO',
  EsBr = 'ES_BR',
  EsBz = 'ES_BZ',
  EsCl = 'ES_CL',
  EsCo = 'ES_CO',
  EsCr = 'ES_CR',
  EsCu = 'ES_CU',
  EsDo = 'ES_DO',
  EsEa = 'ES_EA',
  EsEc = 'ES_EC',
  EsEs = 'ES_ES',
  EsGq = 'ES_GQ',
  EsGt = 'ES_GT',
  EsHn = 'ES_HN',
  EsIc = 'ES_IC',
  EsMx = 'ES_MX',
  EsNi = 'ES_NI',
  EsPa = 'ES_PA',
  EsPe = 'ES_PE',
  EsPh = 'ES_PH',
  EsPr = 'ES_PR',
  EsPy = 'ES_PY',
  EsSv = 'ES_SV',
  EsUs = 'ES_US',
  EsUy = 'ES_UY',
  EsVe = 'ES_VE',
  Et = 'ET',
  EtEe = 'ET_EE',
  Eu = 'EU',
  EuEs = 'EU_ES',
  Ewo = 'EWO',
  EwoCm = 'EWO_CM',
  Fa = 'FA',
  FaAf = 'FA_AF',
  FaIr = 'FA_IR',
  Ff = 'FF',
  FfAdlm = 'FF_ADLM',
  FfAdlmBf = 'FF_ADLM_BF',
  FfAdlmCm = 'FF_ADLM_CM',
  FfAdlmGh = 'FF_ADLM_GH',
  FfAdlmGm = 'FF_ADLM_GM',
  FfAdlmGn = 'FF_ADLM_GN',
  FfAdlmGw = 'FF_ADLM_GW',
  FfAdlmLr = 'FF_ADLM_LR',
  FfAdlmMr = 'FF_ADLM_MR',
  FfAdlmNe = 'FF_ADLM_NE',
  FfAdlmNg = 'FF_ADLM_NG',
  FfAdlmSl = 'FF_ADLM_SL',
  FfAdlmSn = 'FF_ADLM_SN',
  FfLatn = 'FF_LATN',
  FfLatnBf = 'FF_LATN_BF',
  FfLatnCm = 'FF_LATN_CM',
  FfLatnGh = 'FF_LATN_GH',
  FfLatnGm = 'FF_LATN_GM',
  FfLatnGn = 'FF_LATN_GN',
  FfLatnGw = 'FF_LATN_GW',
  FfLatnLr = 'FF_LATN_LR',
  FfLatnMr = 'FF_LATN_MR',
  FfLatnNe = 'FF_LATN_NE',
  FfLatnNg = 'FF_LATN_NG',
  FfLatnSl = 'FF_LATN_SL',
  FfLatnSn = 'FF_LATN_SN',
  Fi = 'FI',
  Fil = 'FIL',
  FilPh = 'FIL_PH',
  FiFi = 'FI_FI',
  Fo = 'FO',
  FoDk = 'FO_DK',
  FoFo = 'FO_FO',
  Fr = 'FR',
  FrBe = 'FR_BE',
  FrBf = 'FR_BF',
  FrBi = 'FR_BI',
  FrBj = 'FR_BJ',
  FrBl = 'FR_BL',
  FrCa = 'FR_CA',
  FrCd = 'FR_CD',
  FrCf = 'FR_CF',
  FrCg = 'FR_CG',
  FrCh = 'FR_CH',
  FrCi = 'FR_CI',
  FrCm = 'FR_CM',
  FrDj = 'FR_DJ',
  FrDz = 'FR_DZ',
  FrFr = 'FR_FR',
  FrGa = 'FR_GA',
  FrGf = 'FR_GF',
  FrGn = 'FR_GN',
  FrGp = 'FR_GP',
  FrGq = 'FR_GQ',
  FrHt = 'FR_HT',
  FrKm = 'FR_KM',
  FrLu = 'FR_LU',
  FrMa = 'FR_MA',
  FrMc = 'FR_MC',
  FrMf = 'FR_MF',
  FrMg = 'FR_MG',
  FrMl = 'FR_ML',
  FrMq = 'FR_MQ',
  FrMr = 'FR_MR',
  FrMu = 'FR_MU',
  FrNc = 'FR_NC',
  FrNe = 'FR_NE',
  FrPf = 'FR_PF',
  FrPm = 'FR_PM',
  FrRe = 'FR_RE',
  FrRw = 'FR_RW',
  FrSc = 'FR_SC',
  FrSn = 'FR_SN',
  FrSy = 'FR_SY',
  FrTd = 'FR_TD',
  FrTg = 'FR_TG',
  FrTn = 'FR_TN',
  FrVu = 'FR_VU',
  FrWf = 'FR_WF',
  FrYt = 'FR_YT',
  Fur = 'FUR',
  FurIt = 'FUR_IT',
  Fy = 'FY',
  FyNl = 'FY_NL',
  Ga = 'GA',
  GaGb = 'GA_GB',
  GaIe = 'GA_IE',
  Gd = 'GD',
  GdGb = 'GD_GB',
  Gl = 'GL',
  GlEs = 'GL_ES',
  Gsw = 'GSW',
  GswCh = 'GSW_CH',
  GswFr = 'GSW_FR',
  GswLi = 'GSW_LI',
  Gu = 'GU',
  Guz = 'GUZ',
  GuzKe = 'GUZ_KE',
  GuIn = 'GU_IN',
  Gv = 'GV',
  GvIm = 'GV_IM',
  Ha = 'HA',
  Haw = 'HAW',
  HawUs = 'HAW_US',
  HaGh = 'HA_GH',
  HaNe = 'HA_NE',
  HaNg = 'HA_NG',
  He = 'HE',
  HeIl = 'HE_IL',
  Hi = 'HI',
  HiIn = 'HI_IN',
  Hr = 'HR',
  HrBa = 'HR_BA',
  HrHr = 'HR_HR',
  Hsb = 'HSB',
  HsbDe = 'HSB_DE',
  Hu = 'HU',
  HuHu = 'HU_HU',
  Hy = 'HY',
  HyAm = 'HY_AM',
  Ia = 'IA',
  Id = 'ID',
  IdId = 'ID_ID',
  Ig = 'IG',
  IgNg = 'IG_NG',
  Ii = 'II',
  IiCn = 'II_CN',
  Is = 'IS',
  IsIs = 'IS_IS',
  It = 'IT',
  ItCh = 'IT_CH',
  ItIt = 'IT_IT',
  ItSm = 'IT_SM',
  ItVa = 'IT_VA',
  Ja = 'JA',
  JaJp = 'JA_JP',
  Jgo = 'JGO',
  JgoCm = 'JGO_CM',
  Jmc = 'JMC',
  JmcTz = 'JMC_TZ',
  Jv = 'JV',
  JvId = 'JV_ID',
  Ka = 'KA',
  Kab = 'KAB',
  KabDz = 'KAB_DZ',
  Kam = 'KAM',
  KamKe = 'KAM_KE',
  KaGe = 'KA_GE',
  Kde = 'KDE',
  KdeTz = 'KDE_TZ',
  Kea = 'KEA',
  KeaCv = 'KEA_CV',
  Khq = 'KHQ',
  KhqMl = 'KHQ_ML',
  Ki = 'KI',
  KiKe = 'KI_KE',
  Kk = 'KK',
  Kkj = 'KKJ',
  KkjCm = 'KKJ_CM',
  KkKz = 'KK_KZ',
  Kl = 'KL',
  Kln = 'KLN',
  KlnKe = 'KLN_KE',
  KlGl = 'KL_GL',
  Km = 'KM',
  KmKh = 'KM_KH',
  Kn = 'KN',
  KnIn = 'KN_IN',
  Ko = 'KO',
  Kok = 'KOK',
  KokIn = 'KOK_IN',
  KoKp = 'KO_KP',
  KoKr = 'KO_KR',
  Ks = 'KS',
  Ksb = 'KSB',
  KsbTz = 'KSB_TZ',
  Ksf = 'KSF',
  KsfCm = 'KSF_CM',
  Ksh = 'KSH',
  KshDe = 'KSH_DE',
  KsArab = 'KS_ARAB',
  KsArabIn = 'KS_ARAB_IN',
  Ku = 'KU',
  KuTr = 'KU_TR',
  Kw = 'KW',
  KwGb = 'KW_GB',
  Ky = 'KY',
  KyKg = 'KY_KG',
  Lag = 'LAG',
  LagTz = 'LAG_TZ',
  Lb = 'LB',
  LbLu = 'LB_LU',
  Lg = 'LG',
  LgUg = 'LG_UG',
  Lkt = 'LKT',
  LktUs = 'LKT_US',
  Ln = 'LN',
  LnAo = 'LN_AO',
  LnCd = 'LN_CD',
  LnCf = 'LN_CF',
  LnCg = 'LN_CG',
  Lo = 'LO',
  LoLa = 'LO_LA',
  Lrc = 'LRC',
  LrcIq = 'LRC_IQ',
  LrcIr = 'LRC_IR',
  Lt = 'LT',
  LtLt = 'LT_LT',
  Lu = 'LU',
  Luo = 'LUO',
  LuoKe = 'LUO_KE',
  Luy = 'LUY',
  LuyKe = 'LUY_KE',
  LuCd = 'LU_CD',
  Lv = 'LV',
  LvLv = 'LV_LV',
  Mai = 'MAI',
  MaiIn = 'MAI_IN',
  Mas = 'MAS',
  MasKe = 'MAS_KE',
  MasTz = 'MAS_TZ',
  Mer = 'MER',
  MerKe = 'MER_KE',
  Mfe = 'MFE',
  MfeMu = 'MFE_MU',
  Mg = 'MG',
  Mgh = 'MGH',
  MghMz = 'MGH_MZ',
  Mgo = 'MGO',
  MgoCm = 'MGO_CM',
  MgMg = 'MG_MG',
  Mi = 'MI',
  MiNz = 'MI_NZ',
  Mk = 'MK',
  MkMk = 'MK_MK',
  Ml = 'ML',
  MlIn = 'ML_IN',
  Mn = 'MN',
  Mni = 'MNI',
  MniBeng = 'MNI_BENG',
  MniBengIn = 'MNI_BENG_IN',
  MnMn = 'MN_MN',
  Mr = 'MR',
  MrIn = 'MR_IN',
  Ms = 'MS',
  MsBn = 'MS_BN',
  MsId = 'MS_ID',
  MsMy = 'MS_MY',
  MsSg = 'MS_SG',
  Mt = 'MT',
  MtMt = 'MT_MT',
  Mua = 'MUA',
  MuaCm = 'MUA_CM',
  My = 'MY',
  MyMm = 'MY_MM',
  Mzn = 'MZN',
  MznIr = 'MZN_IR',
  Naq = 'NAQ',
  NaqNa = 'NAQ_NA',
  Nb = 'NB',
  NbNo = 'NB_NO',
  NbSj = 'NB_SJ',
  Nd = 'ND',
  Nds = 'NDS',
  NdsDe = 'NDS_DE',
  NdsNl = 'NDS_NL',
  NdZw = 'ND_ZW',
  Ne = 'NE',
  NeIn = 'NE_IN',
  NeNp = 'NE_NP',
  Nl = 'NL',
  NlAw = 'NL_AW',
  NlBe = 'NL_BE',
  NlBq = 'NL_BQ',
  NlCw = 'NL_CW',
  NlNl = 'NL_NL',
  NlSr = 'NL_SR',
  NlSx = 'NL_SX',
  Nmg = 'NMG',
  NmgCm = 'NMG_CM',
  Nn = 'NN',
  Nnh = 'NNH',
  NnhCm = 'NNH_CM',
  NnNo = 'NN_NO',
  Nus = 'NUS',
  NusSs = 'NUS_SS',
  Nyn = 'NYN',
  NynUg = 'NYN_UG',
  Om = 'OM',
  OmEt = 'OM_ET',
  OmKe = 'OM_KE',
  Or = 'OR',
  OrIn = 'OR_IN',
  Os = 'OS',
  OsGe = 'OS_GE',
  OsRu = 'OS_RU',
  Pa = 'PA',
  PaArab = 'PA_ARAB',
  PaArabPk = 'PA_ARAB_PK',
  PaGuru = 'PA_GURU',
  PaGuruIn = 'PA_GURU_IN',
  Pcm = 'PCM',
  PcmNg = 'PCM_NG',
  Pl = 'PL',
  PlPl = 'PL_PL',
  Prg = 'PRG',
  Ps = 'PS',
  PsAf = 'PS_AF',
  PsPk = 'PS_PK',
  Pt = 'PT',
  PtAo = 'PT_AO',
  PtBr = 'PT_BR',
  PtCh = 'PT_CH',
  PtCv = 'PT_CV',
  PtGq = 'PT_GQ',
  PtGw = 'PT_GW',
  PtLu = 'PT_LU',
  PtMo = 'PT_MO',
  PtMz = 'PT_MZ',
  PtPt = 'PT_PT',
  PtSt = 'PT_ST',
  PtTl = 'PT_TL',
  Qu = 'QU',
  QuBo = 'QU_BO',
  QuEc = 'QU_EC',
  QuPe = 'QU_PE',
  Rm = 'RM',
  RmCh = 'RM_CH',
  Rn = 'RN',
  RnBi = 'RN_BI',
  Ro = 'RO',
  Rof = 'ROF',
  RofTz = 'ROF_TZ',
  RoMd = 'RO_MD',
  RoRo = 'RO_RO',
  Ru = 'RU',
  RuBy = 'RU_BY',
  RuKg = 'RU_KG',
  RuKz = 'RU_KZ',
  RuMd = 'RU_MD',
  RuRu = 'RU_RU',
  RuUa = 'RU_UA',
  Rw = 'RW',
  Rwk = 'RWK',
  RwkTz = 'RWK_TZ',
  RwRw = 'RW_RW',
  Sah = 'SAH',
  SahRu = 'SAH_RU',
  Saq = 'SAQ',
  SaqKe = 'SAQ_KE',
  Sat = 'SAT',
  SatOlck = 'SAT_OLCK',
  SatOlckIn = 'SAT_OLCK_IN',
  Sbp = 'SBP',
  SbpTz = 'SBP_TZ',
  Sd = 'SD',
  SdArab = 'SD_ARAB',
  SdArabPk = 'SD_ARAB_PK',
  SdDeva = 'SD_DEVA',
  SdDevaIn = 'SD_DEVA_IN',
  Se = 'SE',
  Seh = 'SEH',
  SehMz = 'SEH_MZ',
  Ses = 'SES',
  SesMl = 'SES_ML',
  SeFi = 'SE_FI',
  SeNo = 'SE_NO',
  SeSe = 'SE_SE',
  Sg = 'SG',
  SgCf = 'SG_CF',
  Shi = 'SHI',
  ShiLatn = 'SHI_LATN',
  ShiLatnMa = 'SHI_LATN_MA',
  ShiTfng = 'SHI_TFNG',
  ShiTfngMa = 'SHI_TFNG_MA',
  Si = 'SI',
  SiLk = 'SI_LK',
  Sk = 'SK',
  SkSk = 'SK_SK',
  Sl = 'SL',
  SlSi = 'SL_SI',
  Smn = 'SMN',
  SmnFi = 'SMN_FI',
  Sn = 'SN',
  SnZw = 'SN_ZW',
  So = 'SO',
  SoDj = 'SO_DJ',
  SoEt = 'SO_ET',
  SoKe = 'SO_KE',
  SoSo = 'SO_SO',
  Sq = 'SQ',
  SqAl = 'SQ_AL',
  SqMk = 'SQ_MK',
  SqXk = 'SQ_XK',
  Sr = 'SR',
  SrCyrl = 'SR_CYRL',
  SrCyrlBa = 'SR_CYRL_BA',
  SrCyrlMe = 'SR_CYRL_ME',
  SrCyrlRs = 'SR_CYRL_RS',
  SrCyrlXk = 'SR_CYRL_XK',
  SrLatn = 'SR_LATN',
  SrLatnBa = 'SR_LATN_BA',
  SrLatnMe = 'SR_LATN_ME',
  SrLatnRs = 'SR_LATN_RS',
  SrLatnXk = 'SR_LATN_XK',
  Su = 'SU',
  SuLatn = 'SU_LATN',
  SuLatnId = 'SU_LATN_ID',
  Sv = 'SV',
  SvAx = 'SV_AX',
  SvFi = 'SV_FI',
  SvSe = 'SV_SE',
  Sw = 'SW',
  SwCd = 'SW_CD',
  SwKe = 'SW_KE',
  SwTz = 'SW_TZ',
  SwUg = 'SW_UG',
  Ta = 'TA',
  TaIn = 'TA_IN',
  TaLk = 'TA_LK',
  TaMy = 'TA_MY',
  TaSg = 'TA_SG',
  Te = 'TE',
  Teo = 'TEO',
  TeoKe = 'TEO_KE',
  TeoUg = 'TEO_UG',
  TeIn = 'TE_IN',
  Tg = 'TG',
  TgTj = 'TG_TJ',
  Th = 'TH',
  ThTh = 'TH_TH',
  Ti = 'TI',
  TiEr = 'TI_ER',
  TiEt = 'TI_ET',
  Tk = 'TK',
  TkTm = 'TK_TM',
  To = 'TO',
  ToTo = 'TO_TO',
  Tr = 'TR',
  TrCy = 'TR_CY',
  TrTr = 'TR_TR',
  Tt = 'TT',
  TtRu = 'TT_RU',
  Twq = 'TWQ',
  TwqNe = 'TWQ_NE',
  Tzm = 'TZM',
  TzmMa = 'TZM_MA',
  Ug = 'UG',
  UgCn = 'UG_CN',
  Uk = 'UK',
  UkUa = 'UK_UA',
  Ur = 'UR',
  UrIn = 'UR_IN',
  UrPk = 'UR_PK',
  Uz = 'UZ',
  UzArab = 'UZ_ARAB',
  UzArabAf = 'UZ_ARAB_AF',
  UzCyrl = 'UZ_CYRL',
  UzCyrlUz = 'UZ_CYRL_UZ',
  UzLatn = 'UZ_LATN',
  UzLatnUz = 'UZ_LATN_UZ',
  Vai = 'VAI',
  VaiLatn = 'VAI_LATN',
  VaiLatnLr = 'VAI_LATN_LR',
  VaiVaii = 'VAI_VAII',
  VaiVaiiLr = 'VAI_VAII_LR',
  Vi = 'VI',
  ViVn = 'VI_VN',
  Vo = 'VO',
  Vun = 'VUN',
  VunTz = 'VUN_TZ',
  Wae = 'WAE',
  WaeCh = 'WAE_CH',
  Wo = 'WO',
  WoSn = 'WO_SN',
  Xh = 'XH',
  XhZa = 'XH_ZA',
  Xog = 'XOG',
  XogUg = 'XOG_UG',
  Yav = 'YAV',
  YavCm = 'YAV_CM',
  Yi = 'YI',
  Yo = 'YO',
  YoBj = 'YO_BJ',
  YoNg = 'YO_NG',
  Yue = 'YUE',
  YueHans = 'YUE_HANS',
  YueHansCn = 'YUE_HANS_CN',
  YueHant = 'YUE_HANT',
  YueHantHk = 'YUE_HANT_HK',
  Zgh = 'ZGH',
  ZghMa = 'ZGH_MA',
  Zh = 'ZH',
  ZhHans = 'ZH_HANS',
  ZhHansCn = 'ZH_HANS_CN',
  ZhHansHk = 'ZH_HANS_HK',
  ZhHansMo = 'ZH_HANS_MO',
  ZhHansSg = 'ZH_HANS_SG',
  ZhHant = 'ZH_HANT',
  ZhHantHk = 'ZH_HANT_HK',
  ZhHantMo = 'ZH_HANT_MO',
  ZhHantTw = 'ZH_HANT_TW',
  Zu = 'ZU',
  ZuZa = 'ZU_ZA'
}

export type LanguageDisplay = {
  __typename?: 'LanguageDisplay';
  /** ISO 639 representation of the language name. */
  code: LanguageCodeEnum;
  /** Full name of the language. */
  language: Scalars['String']['output'];
};

export type LimitInfo = {
  __typename?: 'LimitInfo';
  /** Defines the allowed maximum resource usage, null means unlimited. */
  allowedUsage: Limits;
  /** Defines the current resource usage. */
  currentUsage: Limits;
};

export type Limits = {
  __typename?: 'Limits';
  channels?: Maybe<Scalars['Int']['output']>;
  orders?: Maybe<Scalars['Int']['output']>;
  productVariants?: Maybe<Scalars['Int']['output']>;
  staffUsers?: Maybe<Scalars['Int']['output']>;
  warehouses?: Maybe<Scalars['Int']['output']>;
};

/** The manifest definition. */
export type Manifest = {
  __typename?: 'Manifest';
  about?: Maybe<Scalars['String']['output']>;
  appUrl?: Maybe<Scalars['String']['output']>;
  /**
   * The audience that will be included in all JWT tokens for the app.
   *
   * Added in Saleor 3.8.
   */
  audience?: Maybe<Scalars['String']['output']>;
  /**
   * The App's author name.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  author?: Maybe<Scalars['String']['output']>;
  /**
   * URL to iframe with the configuration for the app.
   * @deprecated This field will be removed in Saleor 4.0. Use `appUrl` instead.
   */
  configurationUrl?: Maybe<Scalars['String']['output']>;
  /**
   * Description of the data privacy defined for this app.
   * @deprecated This field will be removed in Saleor 4.0. Use `dataPrivacyUrl` instead.
   */
  dataPrivacy?: Maybe<Scalars['String']['output']>;
  dataPrivacyUrl?: Maybe<Scalars['String']['output']>;
  extensions: Array<AppManifestExtension>;
  homepageUrl?: Maybe<Scalars['String']['output']>;
  identifier: Scalars['String']['output'];
  name: Scalars['String']['output'];
  permissions?: Maybe<Array<Permission>>;
  /**
   * Determines the app's required Saleor version as semver range.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  requiredSaleorVersion?: Maybe<AppManifestRequiredSaleorVersion>;
  supportUrl?: Maybe<Scalars['String']['output']>;
  tokenTargetUrl?: Maybe<Scalars['String']['output']>;
  version: Scalars['String']['output'];
  /**
   * List of the app's webhooks.
   *
   * Added in Saleor 3.5.
   */
  webhooks: Array<AppManifestWebhook>;
};

export type Margin = {
  __typename?: 'Margin';
  start?: Maybe<Scalars['Int']['output']>;
  stop?: Maybe<Scalars['Int']['output']>;
};

/**
 * Determine the mark as paid strategy for the channel.
 *
 *     TRANSACTION_FLOW - new orders marked as paid will receive a
 *     `TransactionItem` object, that will cover the `order.total`.
 *
 *     PAYMENT_FLOW - new orders marked as paid will receive a
 *     `Payment` object, that will cover the `order.total`.
 *
 *
 */
export enum MarkAsPaidStrategyEnum {
  PaymentFlow = 'PAYMENT_FLOW',
  TransactionFlow = 'TRANSACTION_FLOW'
}

/** An enumeration. */
export enum MeasurementUnitsEnum {
  AcreFt = 'ACRE_FT',
  AcreIn = 'ACRE_IN',
  Cm = 'CM',
  CubicCentimeter = 'CUBIC_CENTIMETER',
  CubicDecimeter = 'CUBIC_DECIMETER',
  CubicFoot = 'CUBIC_FOOT',
  CubicInch = 'CUBIC_INCH',
  CubicMeter = 'CUBIC_METER',
  CubicMillimeter = 'CUBIC_MILLIMETER',
  CubicYard = 'CUBIC_YARD',
  FlOz = 'FL_OZ',
  Ft = 'FT',
  G = 'G',
  Inch = 'INCH',
  Kg = 'KG',
  Km = 'KM',
  Lb = 'LB',
  Liter = 'LITER',
  M = 'M',
  Oz = 'OZ',
  Pint = 'PINT',
  Qt = 'QT',
  SqCm = 'SQ_CM',
  SqFt = 'SQ_FT',
  SqInch = 'SQ_INCH',
  SqKm = 'SQ_KM',
  SqM = 'SQ_M',
  SqYd = 'SQ_YD',
  Tonne = 'TONNE',
  Yd = 'YD'
}

export type MeasurementUnitsEnumFilterInput = {
  /** The value equal to. */
  eq?: InputMaybe<MeasurementUnitsEnum>;
  /** The value included in. */
  oneOf?: InputMaybe<Array<MeasurementUnitsEnum>>;
};

export enum MediaChoicesSortField {
  /** Sort media by ID. */
  Id = 'ID'
}

export type MediaInput = {
  /** Alt text for a product media. */
  alt?: InputMaybe<Scalars['String']['input']>;
  /** Represents an image file in a multipart request. */
  image?: InputMaybe<Scalars['Upload']['input']>;
  /** Represents an URL to an external media. */
  mediaUrl?: InputMaybe<Scalars['String']['input']>;
};

export type MediaSortingInput = {
  /** Specifies the direction in which to sort media. */
  direction: OrderDirection;
  /** Sort media by the selected field. */
  field: MediaChoicesSortField;
};

/** Represents a single menu - an object that is used to help navigate through the store. */
export type Menu = Node & ObjectWithMetadata & {
  __typename?: 'Menu';
  id: Scalars['ID']['output'];
  items?: Maybe<Array<MenuItem>>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  slug: Scalars['String']['output'];
};


/** Represents a single menu - an object that is used to help navigate through the store. */
export type MenuMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single menu - an object that is used to help navigate through the store. */
export type MenuMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a single menu - an object that is used to help navigate through the store. */
export type MenuPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single menu - an object that is used to help navigate through the store. */
export type MenuPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Deletes menus.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuBulkDelete = {
  __typename?: 'MenuBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<MenuError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

export type MenuCountableConnection = {
  __typename?: 'MenuCountableConnection';
  edges: Array<MenuCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type MenuCountableEdge = {
  __typename?: 'MenuCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Menu;
};

/**
 * Creates a new Menu.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuCreate = {
  __typename?: 'MenuCreate';
  errors: Array<MenuError>;
  menu?: Maybe<Menu>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

export type MenuCreateInput = {
  /** List of menu items. */
  items?: InputMaybe<Array<MenuItemInput>>;
  /** Name of the menu. */
  name: Scalars['String']['input'];
  /** Slug of the menu. Will be generated if not provided. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new menu is created.
 *
 * Added in Saleor 3.4.
 */
export type MenuCreated = Event & {
  __typename?: 'MenuCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu the event relates to. */
  menu?: Maybe<Menu>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new menu is created.
 *
 * Added in Saleor 3.4.
 */
export type MenuCreatedMenuArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a menu.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuDelete = {
  __typename?: 'MenuDelete';
  errors: Array<MenuError>;
  menu?: Maybe<Menu>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

/**
 * Event sent when menu is deleted.
 *
 * Added in Saleor 3.4.
 */
export type MenuDeleted = Event & {
  __typename?: 'MenuDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu the event relates to. */
  menu?: Maybe<Menu>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when menu is deleted.
 *
 * Added in Saleor 3.4.
 */
export type MenuDeletedMenuArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type MenuError = {
  __typename?: 'MenuError';
  /** The error code. */
  code: MenuErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum MenuErrorCode {
  CannotAssignNode = 'CANNOT_ASSIGN_NODE',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidMenuItem = 'INVALID_MENU_ITEM',
  NotFound = 'NOT_FOUND',
  NoMenuItemProvided = 'NO_MENU_ITEM_PROVIDED',
  Required = 'REQUIRED',
  TooManyMenuItems = 'TOO_MANY_MENU_ITEMS',
  Unique = 'UNIQUE'
}

export type MenuFilterInput = {
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  slug?: InputMaybe<Array<Scalars['String']['input']>>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type MenuInput = {
  /** Name of the menu. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Slug of the menu. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItem = Node & ObjectWithMetadata & {
  __typename?: 'MenuItem';
  category?: Maybe<Category>;
  children?: Maybe<Array<MenuItem>>;
  /** A collection associated with this menu item. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  collection?: Maybe<Collection>;
  id: Scalars['ID']['output'];
  level: Scalars['Int']['output'];
  menu: Menu;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** A page associated with this menu item. Requires one of the following permissions to include unpublished items: MANAGE_PAGES. */
  page?: Maybe<Page>;
  parent?: Maybe<MenuItem>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Returns translated menu item fields for the given language code. */
  translation?: Maybe<MenuItemTranslation>;
  /** URL to the menu item. */
  url?: Maybe<Scalars['String']['output']>;
};


/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItemMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItemMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItemPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItemPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a single item of the related menu. Can store categories, collection or pages. */
export type MenuItemTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Deletes menu items.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuItemBulkDelete = {
  __typename?: 'MenuItemBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<MenuError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

export type MenuItemCountableConnection = {
  __typename?: 'MenuItemCountableConnection';
  edges: Array<MenuItemCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type MenuItemCountableEdge = {
  __typename?: 'MenuItemCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: MenuItem;
};

/**
 * Creates a new menu item.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuItemCreate = {
  __typename?: 'MenuItemCreate';
  errors: Array<MenuError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
  menuItem?: Maybe<MenuItem>;
};

export type MenuItemCreateInput = {
  /** Category to which item points. */
  category?: InputMaybe<Scalars['ID']['input']>;
  /** Collection to which item points. */
  collection?: InputMaybe<Scalars['ID']['input']>;
  /** Menu to which item belongs. */
  menu: Scalars['ID']['input'];
  /** Name of the menu item. */
  name: Scalars['String']['input'];
  /** Page to which item points. */
  page?: InputMaybe<Scalars['ID']['input']>;
  /** ID of the parent menu. If empty, menu will be top level menu. */
  parent?: InputMaybe<Scalars['ID']['input']>;
  /** URL of the pointed item. */
  url?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new menu item is created.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemCreated = Event & {
  __typename?: 'MenuItemCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu item the event relates to. */
  menuItem?: Maybe<MenuItem>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new menu item is created.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemCreatedMenuItemArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a menu item.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuItemDelete = {
  __typename?: 'MenuItemDelete';
  errors: Array<MenuError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
  menuItem?: Maybe<MenuItem>;
};

/**
 * Event sent when menu item is deleted.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemDeleted = Event & {
  __typename?: 'MenuItemDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu item the event relates to. */
  menuItem?: Maybe<MenuItem>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when menu item is deleted.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemDeletedMenuItemArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type MenuItemFilterInput = {
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
};

export type MenuItemInput = {
  /** Category to which item points. */
  category?: InputMaybe<Scalars['ID']['input']>;
  /** Collection to which item points. */
  collection?: InputMaybe<Scalars['ID']['input']>;
  /** Name of the menu item. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Page to which item points. */
  page?: InputMaybe<Scalars['ID']['input']>;
  /** URL of the pointed item. */
  url?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Moves items of menus.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuItemMove = {
  __typename?: 'MenuItemMove';
  errors: Array<MenuError>;
  /** Assigned menu to move within. */
  menu?: Maybe<Menu>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

export type MenuItemMoveInput = {
  /** The menu item ID to move. */
  itemId: Scalars['ID']['input'];
  /** ID of the parent menu. If empty, menu will be top level menu. */
  parentId?: InputMaybe<Scalars['ID']['input']>;
  /** The new relative sorting position of the item (from -inf to +inf). 1 moves the item one position forward, -1 moves the item one position backward, 0 leaves the item unchanged. */
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
};

export type MenuItemSortingInput = {
  /** Specifies the direction in which to sort menu items. */
  direction: OrderDirection;
  /** Sort menu items by the selected field. */
  field: MenuItemsSortField;
};

export type MenuItemTranslatableContent = Node & {
  __typename?: 'MenuItemTranslatableContent';
  id: Scalars['ID']['output'];
  /**
   * Represents a single item of the related menu. Can store categories, collection or pages.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  menuItem?: Maybe<MenuItem>;
  name: Scalars['String']['output'];
  /** Returns translated menu item fields for the given language code. */
  translation?: Maybe<MenuItemTranslation>;
};


export type MenuItemTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a menu item.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type MenuItemTranslate = {
  __typename?: 'MenuItemTranslate';
  errors: Array<TranslationError>;
  menuItem?: Maybe<MenuItem>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type MenuItemTranslation = Node & {
  __typename?: 'MenuItemTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name: Scalars['String']['output'];
};

/**
 * Updates a menu item.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuItemUpdate = {
  __typename?: 'MenuItemUpdate';
  errors: Array<MenuError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
  menuItem?: Maybe<MenuItem>;
};

/**
 * Event sent when menu item is updated.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemUpdated = Event & {
  __typename?: 'MenuItemUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu item the event relates to. */
  menuItem?: Maybe<MenuItem>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when menu item is updated.
 *
 * Added in Saleor 3.4.
 */
export type MenuItemUpdatedMenuItemArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export enum MenuItemsSortField {
  /** Sort menu items by name. */
  Name = 'NAME'
}

export enum MenuSortField {
  /** Sort menus by items count. */
  ItemsCount = 'ITEMS_COUNT',
  /** Sort menus by name. */
  Name = 'NAME'
}

export type MenuSortingInput = {
  /** Specifies the direction in which to sort menus. */
  direction: OrderDirection;
  /** Sort menus by the selected field. */
  field: MenuSortField;
};

/**
 * Updates a menu.
 *
 * Requires one of the following permissions: MANAGE_MENUS.
 */
export type MenuUpdate = {
  __typename?: 'MenuUpdate';
  errors: Array<MenuError>;
  menu?: Maybe<Menu>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  menuErrors: Array<MenuError>;
};

/**
 * Event sent when menu is updated.
 *
 * Added in Saleor 3.4.
 */
export type MenuUpdated = Event & {
  __typename?: 'MenuUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The menu the event relates to. */
  menu?: Maybe<Menu>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when menu is updated.
 *
 * Added in Saleor 3.4.
 */
export type MenuUpdatedMenuArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type MetadataError = {
  __typename?: 'MetadataError';
  /** The error code. */
  code: MetadataErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum MetadataErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  NotUpdated = 'NOT_UPDATED',
  Required = 'REQUIRED'
}

export type MetadataFilter = {
  /** Key of a metadata item. */
  key: Scalars['String']['input'];
  /** Value of a metadata item. */
  value?: InputMaybe<Scalars['String']['input']>;
};

export type MetadataInput = {
  /** Key of a metadata item. */
  key: Scalars['String']['input'];
  /** Value of a metadata item. */
  value: Scalars['String']['input'];
};

export type MetadataItem = {
  __typename?: 'MetadataItem';
  /** Key of a metadata item. */
  key: Scalars['String']['output'];
  /** Value of a metadata item. */
  value: Scalars['String']['output'];
};

/** Represents amount of money in specific currency. */
export type Money = {
  __typename?: 'Money';
  /** Amount of money. */
  amount: Scalars['Float']['output'];
  /** Currency code. */
  currency: Scalars['String']['output'];
};

export type MoneyInput = {
  /** Amount of money. */
  amount: Scalars['PositiveDecimal']['input'];
  /** Currency code. */
  currency: Scalars['String']['input'];
};

/** Represents a range of amounts of money. */
export type MoneyRange = {
  __typename?: 'MoneyRange';
  /** Lower bound of a price range. */
  start?: Maybe<Money>;
  /** Upper bound of a price range. */
  stop?: Maybe<Money>;
};

export type MoveProductInput = {
  /** The ID of the product to move. */
  productId: Scalars['ID']['input'];
  /** The relative sorting position of the product (from -inf to +inf) starting from the first given product's actual position.1 moves the item one position forward, -1 moves the item one position backward, 0 leaves the item unchanged. */
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
};

export type Mutation = {
  __typename?: 'Mutation';
  /**
   * Create a new address for the customer.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  accountAddressCreate?: Maybe<AccountAddressCreate>;
  /** Delete an address of the logged-in user. Requires one of the following permissions: MANAGE_USERS, IS_OWNER. */
  accountAddressDelete?: Maybe<AccountAddressDelete>;
  /** Updates an address of the logged-in user. Requires one of the following permissions: MANAGE_USERS, IS_OWNER. */
  accountAddressUpdate?: Maybe<AccountAddressUpdate>;
  /**
   * Remove user account.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  accountDelete?: Maybe<AccountDelete>;
  /** Register a new user. */
  accountRegister?: Maybe<AccountRegister>;
  /**
   * Sends an email with the account removal link for the logged-in user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  accountRequestDeletion?: Maybe<AccountRequestDeletion>;
  /**
   * Sets a default address for the authenticated user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  accountSetDefaultAddress?: Maybe<AccountSetDefaultAddress>;
  /**
   * Updates the account of the logged-in user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  accountUpdate?: Maybe<AccountUpdate>;
  /**
   * Creates user address.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  addressCreate?: Maybe<AddressCreate>;
  /**
   * Deletes an address.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  addressDelete?: Maybe<AddressDelete>;
  /**
   * Sets a default address for the given user.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  addressSetDefault?: Maybe<AddressSetDefault>;
  /**
   * Updates an address.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  addressUpdate?: Maybe<AddressUpdate>;
  /**
   * Activate the app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appActivate?: Maybe<AppActivate>;
  /** Creates a new app. Requires the following permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS. */
  appCreate?: Maybe<AppCreate>;
  /**
   * Deactivate the app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appDeactivate?: Maybe<AppDeactivate>;
  /**
   * Deletes an app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appDelete?: Maybe<AppDelete>;
  /**
   * Delete failed installation.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appDeleteFailedInstallation?: Maybe<AppDeleteFailedInstallation>;
  /**
   * Fetch and validate manifest.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appFetchManifest?: Maybe<AppFetchManifest>;
  /** Install new app by using app manifest. Requires the following permissions: AUTHENTICATED_STAFF_USER and MANAGE_APPS. */
  appInstall?: Maybe<AppInstall>;
  /**
   * Retry failed installation of new app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appRetryInstall?: Maybe<AppRetryInstall>;
  /**
   * Creates a new token.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appTokenCreate?: Maybe<AppTokenCreate>;
  /**
   * Deletes an authentication token assigned to app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appTokenDelete?: Maybe<AppTokenDelete>;
  /** Verify provided app token. */
  appTokenVerify?: Maybe<AppTokenVerify>;
  /**
   * Updates an existing app.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appUpdate?: Maybe<AppUpdate>;
  /**
   * Assigns storefront's navigation menus.
   *
   * Requires one of the following permissions: MANAGE_MENUS, MANAGE_SETTINGS.
   */
  assignNavigation?: Maybe<AssignNavigation>;
  /**
   * Add shipping zone to given warehouse.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  assignWarehouseShippingZone?: Maybe<WarehouseShippingZoneAssign>;
  /**
   * Deletes attributes.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  attributeBulkDelete?: Maybe<AttributeBulkDelete>;
  /** Creates an attribute. */
  attributeCreate?: Maybe<AttributeCreate>;
  /**
   * Deletes an attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  attributeDelete?: Maybe<AttributeDelete>;
  /**
   * Reorder the values of an attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  attributeReorderValues?: Maybe<AttributeReorderValues>;
  /**
   * Creates/updates translations for an attribute.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  attributeTranslate?: Maybe<AttributeTranslate>;
  /**
   * Updates attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  attributeUpdate?: Maybe<AttributeUpdate>;
  /**
   * Deletes values of attributes.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  attributeValueBulkDelete?: Maybe<AttributeValueBulkDelete>;
  /**
   * Creates a value for an attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  attributeValueCreate?: Maybe<AttributeValueCreate>;
  /**
   * Deletes a value of an attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  attributeValueDelete?: Maybe<AttributeValueDelete>;
  /**
   * Creates/updates translations for an attribute value.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  attributeValueTranslate?: Maybe<AttributeValueTranslate>;
  /**
   * Updates value of an attribute.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  attributeValueUpdate?: Maybe<AttributeValueUpdate>;
  /**
   * Deletes categories.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  categoryBulkDelete?: Maybe<CategoryBulkDelete>;
  /**
   * Creates a new category.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  categoryCreate?: Maybe<CategoryCreate>;
  /**
   * Deletes a category.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  categoryDelete?: Maybe<CategoryDelete>;
  /**
   * Creates/updates translations for a category.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  categoryTranslate?: Maybe<CategoryTranslate>;
  /**
   * Updates a category.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  categoryUpdate?: Maybe<CategoryUpdate>;
  /**
   * Activate a channel.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  channelActivate?: Maybe<ChannelActivate>;
  /**
   * Creates new channel.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  channelCreate?: Maybe<ChannelCreate>;
  /**
   * Deactivate a channel.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  channelDeactivate?: Maybe<ChannelDeactivate>;
  /**
   * Delete a channel. Orders associated with the deleted channel will be moved to the target channel. Checkouts, product availability, and pricing will be removed.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  channelDelete?: Maybe<ChannelDelete>;
  /**
   * Reorder the warehouses of a channel.
   *
   * Added in Saleor 3.7.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   */
  channelReorderWarehouses?: Maybe<ChannelReorderWarehouses>;
  /**
   * Update a channel.
   *
   * Requires one of the following permissions: MANAGE_CHANNELS.
   * Requires one of the following permissions when updating only orderSettings field: MANAGE_CHANNELS, MANAGE_ORDERS.
   */
  channelUpdate?: Maybe<ChannelUpdate>;
  /** Adds a gift card or a voucher to a checkout. */
  checkoutAddPromoCode?: Maybe<CheckoutAddPromoCode>;
  /** Update billing address in the existing checkout. */
  checkoutBillingAddressUpdate?: Maybe<CheckoutBillingAddressUpdate>;
  /** Completes the checkout. As a result a new order is created and a payment charge is made. This action requires a successful payment before it can be performed. In case additional confirmation step as 3D secure is required confirmationNeeded flag will be set to True and no order created until payment is confirmed with second call of this mutation. */
  checkoutComplete?: Maybe<CheckoutComplete>;
  /** Create a new checkout. */
  checkoutCreate?: Maybe<CheckoutCreate>;
  /**
   * Create new checkout from existing order.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  checkoutCreateFromOrder?: Maybe<CheckoutCreateFromOrder>;
  /**
   * Sets the customer as the owner of the checkout.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_USER.
   */
  checkoutCustomerAttach?: Maybe<CheckoutCustomerAttach>;
  /**
   * Removes the user assigned as the owner of the checkout.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_USER.
   */
  checkoutCustomerDetach?: Maybe<CheckoutCustomerDetach>;
  /**
   * Updates the delivery method (shipping method or pick up point) of the checkout.
   *
   * Added in Saleor 3.1.
   */
  checkoutDeliveryMethodUpdate?: Maybe<CheckoutDeliveryMethodUpdate>;
  /** Updates email address in the existing checkout object. */
  checkoutEmailUpdate?: Maybe<CheckoutEmailUpdate>;
  /** Update language code in the existing checkout. */
  checkoutLanguageCodeUpdate?: Maybe<CheckoutLanguageCodeUpdate>;
  /**
   * Deletes a CheckoutLine.
   * @deprecated This field will be removed in Saleor 4.0. Use `checkoutLinesDelete` instead.
   */
  checkoutLineDelete?: Maybe<CheckoutLineDelete>;
  /** Adds a checkout line to the existing checkout.If line was already in checkout, its quantity will be increased. */
  checkoutLinesAdd?: Maybe<CheckoutLinesAdd>;
  /** Deletes checkout lines. */
  checkoutLinesDelete?: Maybe<CheckoutLinesDelete>;
  /** Updates checkout line in the existing checkout. */
  checkoutLinesUpdate?: Maybe<CheckoutLinesUpdate>;
  /** Create a new payment for given checkout. */
  checkoutPaymentCreate?: Maybe<CheckoutPaymentCreate>;
  /** Remove a gift card or a voucher from a checkout. */
  checkoutRemovePromoCode?: Maybe<CheckoutRemovePromoCode>;
  /** Update shipping address in the existing checkout. */
  checkoutShippingAddressUpdate?: Maybe<CheckoutShippingAddressUpdate>;
  /**
   * Updates the shipping method of the checkout.
   * @deprecated This field will be removed in Saleor 4.0. Use `checkoutDeliveryMethodUpdate` instead.
   */
  checkoutShippingMethodUpdate?: Maybe<CheckoutShippingMethodUpdate>;
  /**
   * Adds products to a collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionAddProducts?: Maybe<CollectionAddProducts>;
  /**
   * Deletes collections.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionBulkDelete?: Maybe<CollectionBulkDelete>;
  /**
   * Manage collection's availability in channels.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionChannelListingUpdate?: Maybe<CollectionChannelListingUpdate>;
  /**
   * Creates a new collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionCreate?: Maybe<CollectionCreate>;
  /**
   * Deletes a collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionDelete?: Maybe<CollectionDelete>;
  /**
   * Remove products from a collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionRemoveProducts?: Maybe<CollectionRemoveProducts>;
  /**
   * Reorder the products of a collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionReorderProducts?: Maybe<CollectionReorderProducts>;
  /**
   * Creates/updates translations for a collection.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  collectionTranslate?: Maybe<CollectionTranslate>;
  /**
   * Updates a collection.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  collectionUpdate?: Maybe<CollectionUpdate>;
  /** Confirm user account with token sent by email during registration. */
  confirmAccount?: Maybe<ConfirmAccount>;
  /**
   * Confirm the email change of the logged-in user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  confirmEmailChange?: Maybe<ConfirmEmailChange>;
  /**
   * Creates new warehouse.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  createWarehouse?: Maybe<WarehouseCreate>;
  /**
   * Deletes customers.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  customerBulkDelete?: Maybe<CustomerBulkDelete>;
  /**
   * Updates customers.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  customerBulkUpdate?: Maybe<CustomerBulkUpdate>;
  /**
   * Creates a new customer.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  customerCreate?: Maybe<CustomerCreate>;
  /**
   * Deletes a customer.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  customerDelete?: Maybe<CustomerDelete>;
  /**
   * Updates an existing customer.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  customerUpdate?: Maybe<CustomerUpdate>;
  /** Delete metadata of an object. To use it, you need to have access to the modified object. */
  deleteMetadata?: Maybe<DeleteMetadata>;
  /** Delete object's private metadata. To use it, you need to be an authenticated staff user or an app and have access to the modified object. */
  deletePrivateMetadata?: Maybe<DeletePrivateMetadata>;
  /**
   * Deletes selected warehouse.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  deleteWarehouse?: Maybe<WarehouseDelete>;
  /**
   * Create new digital content. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContentCreate?: Maybe<DigitalContentCreate>;
  /**
   * Remove digital content assigned to given variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContentDelete?: Maybe<DigitalContentDelete>;
  /**
   * Update digital content.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContentUpdate?: Maybe<DigitalContentUpdate>;
  /**
   * Generate new URL to digital content.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContentUrlCreate?: Maybe<DigitalContentUrlCreate>;
  /**
   * Deletes draft orders.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrderBulkDelete?: Maybe<DraftOrderBulkDelete>;
  /**
   * Completes creating an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrderComplete?: Maybe<DraftOrderComplete>;
  /**
   * Creates a new draft order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrderCreate?: Maybe<DraftOrderCreate>;
  /**
   * Deletes a draft order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrderDelete?: Maybe<DraftOrderDelete>;
  /**
   * Deletes order lines.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  draftOrderLinesBulkDelete?: Maybe<DraftOrderLinesBulkDelete>;
  /**
   * Updates a draft order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrderUpdate?: Maybe<DraftOrderUpdate>;
  /**
   * Retries event delivery.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  eventDeliveryRetry?: Maybe<EventDeliveryRetry>;
  /**
   * Export gift cards to csv file.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  exportGiftCards?: Maybe<ExportGiftCards>;
  /**
   * Export products to csv file.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  exportProducts?: Maybe<ExportProducts>;
  /** Prepare external authentication URL for user by custom plugin. */
  externalAuthenticationUrl?: Maybe<ExternalAuthenticationUrl>;
  /** Logout user by custom plugin. */
  externalLogout?: Maybe<ExternalLogout>;
  /**
   * Trigger sending a notification with the notify plugin method. Serializes nodes provided as ids parameter and includes this data in the notification payload.
   *
   * Added in Saleor 3.1.
   */
  externalNotificationTrigger?: Maybe<ExternalNotificationTrigger>;
  /** Obtain external access tokens for user by custom plugin. */
  externalObtainAccessTokens?: Maybe<ExternalObtainAccessTokens>;
  /** Refresh user's access by custom plugin. */
  externalRefresh?: Maybe<ExternalRefresh>;
  /** Verify external authentication data by plugin. */
  externalVerify?: Maybe<ExternalVerify>;
  /**
   * Upload a file. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  fileUpload?: Maybe<FileUpload>;
  /**
   * Activate a gift card.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardActivate?: Maybe<GiftCardActivate>;
  /**
   * Adds note to the gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardAddNote?: Maybe<GiftCardAddNote>;
  /**
   * Activate gift cards.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardBulkActivate?: Maybe<GiftCardBulkActivate>;
  /**
   * Create gift cards.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardBulkCreate?: Maybe<GiftCardBulkCreate>;
  /**
   * Deactivate gift cards.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardBulkDeactivate?: Maybe<GiftCardBulkDeactivate>;
  /**
   * Delete gift cards.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardBulkDelete?: Maybe<GiftCardBulkDelete>;
  /**
   * Creates a new gift card.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardCreate?: Maybe<GiftCardCreate>;
  /**
   * Deactivate a gift card.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardDeactivate?: Maybe<GiftCardDeactivate>;
  /**
   * Delete gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardDelete?: Maybe<GiftCardDelete>;
  /**
   * Resend a gift card.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardResend?: Maybe<GiftCardResend>;
  /**
   * Update gift card settings.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardSettingsUpdate?: Maybe<GiftCardSettingsUpdate>;
  /**
   * Update a gift card.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardUpdate?: Maybe<GiftCardUpdate>;
  /**
   * Creates a ready to send invoice.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceCreate?: Maybe<InvoiceCreate>;
  /**
   * Deletes an invoice.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceDelete?: Maybe<InvoiceDelete>;
  /**
   * Request an invoice for the order using plugin.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceRequest?: Maybe<InvoiceRequest>;
  /**
   * Requests deletion of an invoice.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceRequestDelete?: Maybe<InvoiceRequestDelete>;
  /**
   * Send an invoice notification to the customer.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceSendNotification?: Maybe<InvoiceSendNotification>;
  /**
   * Updates an invoice.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  invoiceUpdate?: Maybe<InvoiceUpdate>;
  /**
   * Deletes menus.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuBulkDelete?: Maybe<MenuBulkDelete>;
  /**
   * Creates a new Menu.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuCreate?: Maybe<MenuCreate>;
  /**
   * Deletes a menu.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuDelete?: Maybe<MenuDelete>;
  /**
   * Deletes menu items.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuItemBulkDelete?: Maybe<MenuItemBulkDelete>;
  /**
   * Creates a new menu item.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuItemCreate?: Maybe<MenuItemCreate>;
  /**
   * Deletes a menu item.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuItemDelete?: Maybe<MenuItemDelete>;
  /**
   * Moves items of menus.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuItemMove?: Maybe<MenuItemMove>;
  /**
   * Creates/updates translations for a menu item.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  menuItemTranslate?: Maybe<MenuItemTranslate>;
  /**
   * Updates a menu item.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuItemUpdate?: Maybe<MenuItemUpdate>;
  /**
   * Updates a menu.
   *
   * Requires one of the following permissions: MANAGE_MENUS.
   */
  menuUpdate?: Maybe<MenuUpdate>;
  /**
   * Adds note to the order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderAddNote?: Maybe<OrderAddNote>;
  /**
   * Cancels orders.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderBulkCancel?: Maybe<OrderBulkCancel>;
  /**
   * Cancel an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderCancel?: Maybe<OrderCancel>;
  /**
   * Capture an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderCapture?: Maybe<OrderCapture>;
  /**
   * Confirms an unconfirmed order by changing status to unfulfilled.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderConfirm?: Maybe<OrderConfirm>;
  /**
   * Create new order from existing checkout. Requires the following permissions: AUTHENTICATED_APP and HANDLE_CHECKOUTS.
   *
   * Added in Saleor 3.2.
   */
  orderCreateFromCheckout?: Maybe<OrderCreateFromCheckout>;
  /**
   * Adds discount to the order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderDiscountAdd?: Maybe<OrderDiscountAdd>;
  /**
   * Remove discount from the order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderDiscountDelete?: Maybe<OrderDiscountDelete>;
  /**
   * Update discount for the order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderDiscountUpdate?: Maybe<OrderDiscountUpdate>;
  /**
   * Creates new fulfillments for an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfill?: Maybe<OrderFulfill>;
  /**
   * Approve existing fulfillment.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfillmentApprove?: Maybe<FulfillmentApprove>;
  /**
   * Cancels existing fulfillment and optionally restocks items.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfillmentCancel?: Maybe<FulfillmentCancel>;
  /**
   * Refund products.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfillmentRefundProducts?: Maybe<FulfillmentRefundProducts>;
  /**
   * Return products.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfillmentReturnProducts?: Maybe<FulfillmentReturnProducts>;
  /**
   * Updates a fulfillment for an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderFulfillmentUpdateTracking?: Maybe<FulfillmentUpdateTracking>;
  /**
   * Adds granted refund to the order.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderGrantRefundCreate?: Maybe<OrderGrantRefundCreate>;
  /**
   * Updates granted refund.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderGrantRefundUpdate?: Maybe<OrderGrantRefundUpdate>;
  /**
   * Deletes an order line from an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderLineDelete?: Maybe<OrderLineDelete>;
  /**
   * Remove discount applied to the order line.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderLineDiscountRemove?: Maybe<OrderLineDiscountRemove>;
  /**
   * Update discount for the order line.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderLineDiscountUpdate?: Maybe<OrderLineDiscountUpdate>;
  /**
   * Updates an order line of an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderLineUpdate?: Maybe<OrderLineUpdate>;
  /**
   * Create order lines for an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderLinesCreate?: Maybe<OrderLinesCreate>;
  /**
   * Mark order as manually paid.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderMarkAsPaid?: Maybe<OrderMarkAsPaid>;
  /**
   * Refund an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderRefund?: Maybe<OrderRefund>;
  /**
   * Update shop order settings across all channels. Returns `orderSettings` for the first `channel` in alphabetical order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   * @deprecated
   *
   * DEPRECATED: this mutation will be removed in Saleor 4.0. Use `channelUpdate` mutation instead.
   */
  orderSettingsUpdate?: Maybe<OrderSettingsUpdate>;
  /**
   * Updates an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderUpdate?: Maybe<OrderUpdate>;
  /**
   * Updates a shipping method of the order. Requires shipping method ID to update, when null is passed then currently assigned shipping method is removed.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderUpdateShipping?: Maybe<OrderUpdateShipping>;
  /**
   * Void an order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orderVoid?: Maybe<OrderVoid>;
  /**
   * Assign attributes to a given page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageAttributeAssign?: Maybe<PageAttributeAssign>;
  /**
   * Unassign attributes from a given page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageAttributeUnassign?: Maybe<PageAttributeUnassign>;
  /**
   * Deletes pages.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageBulkDelete?: Maybe<PageBulkDelete>;
  /**
   * Publish pages.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageBulkPublish?: Maybe<PageBulkPublish>;
  /**
   * Creates a new page.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageCreate?: Maybe<PageCreate>;
  /**
   * Deletes a page.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageDelete?: Maybe<PageDelete>;
  /**
   * Reorder page attribute values.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageReorderAttributeValues?: Maybe<PageReorderAttributeValues>;
  /**
   * Creates/updates translations for a page.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  pageTranslate?: Maybe<PageTranslate>;
  /**
   * Delete page types.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageTypeBulkDelete?: Maybe<PageTypeBulkDelete>;
  /**
   * Create a new page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageTypeCreate?: Maybe<PageTypeCreate>;
  /**
   * Delete a page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageTypeDelete?: Maybe<PageTypeDelete>;
  /**
   * Reorder the attributes of a page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageTypeReorderAttributes?: Maybe<PageTypeReorderAttributes>;
  /**
   * Update page type.
   *
   * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  pageTypeUpdate?: Maybe<PageTypeUpdate>;
  /**
   * Updates an existing page.
   *
   * Requires one of the following permissions: MANAGE_PAGES.
   */
  pageUpdate?: Maybe<PageUpdate>;
  /**
   * Change the password of the logged in user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  passwordChange?: Maybe<PasswordChange>;
  /**
   * Captures the authorized payment amount.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  paymentCapture?: Maybe<PaymentCapture>;
  /** Check payment balance. */
  paymentCheckBalance?: Maybe<PaymentCheckBalance>;
  /**
   * Initializes a payment gateway session. It triggers the webhook `PAYMENT_GATEWAY_INITIALIZE_SESSION`, to the requested `paymentGateways`. If `paymentGateways` is not provided, the webhook will be send to all subscribed payment gateways.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  paymentGatewayInitialize?: Maybe<PaymentGatewayInitialize>;
  /** Initializes payment process when it is required by gateway. */
  paymentInitialize?: Maybe<PaymentInitialize>;
  /**
   * Refunds the captured payment amount.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  paymentRefund?: Maybe<PaymentRefund>;
  /**
   * Voids the authorized payment.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  paymentVoid?: Maybe<PaymentVoid>;
  /**
   * Create new permission group. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  permissionGroupCreate?: Maybe<PermissionGroupCreate>;
  /**
   * Delete permission group. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  permissionGroupDelete?: Maybe<PermissionGroupDelete>;
  /**
   * Update permission group. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  permissionGroupUpdate?: Maybe<PermissionGroupUpdate>;
  /**
   * Update plugin configuration.
   *
   * Requires one of the following permissions: MANAGE_PLUGINS.
   */
  pluginUpdate?: Maybe<PluginUpdate>;
  /**
   * Assign attributes to a given product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productAttributeAssign?: Maybe<ProductAttributeAssign>;
  /**
   * Update attributes assigned to product variant for given product type.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productAttributeAssignmentUpdate?: Maybe<ProductAttributeAssignmentUpdate>;
  /**
   * Un-assign attributes from a given product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productAttributeUnassign?: Maybe<ProductAttributeUnassign>;
  /**
   * Creates products.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productBulkCreate?: Maybe<ProductBulkCreate>;
  /**
   * Deletes products.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productBulkDelete?: Maybe<ProductBulkDelete>;
  /**
   * Manage product's availability in channels.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productChannelListingUpdate?: Maybe<ProductChannelListingUpdate>;
  /**
   * Creates a new product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productCreate?: Maybe<ProductCreate>;
  /**
   * Deletes a product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productDelete?: Maybe<ProductDelete>;
  /**
   * Deletes product media.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productMediaBulkDelete?: Maybe<ProductMediaBulkDelete>;
  /**
   * Create a media object (image or video URL) associated with product. For image, this mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productMediaCreate?: Maybe<ProductMediaCreate>;
  /**
   * Deletes a product media.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productMediaDelete?: Maybe<ProductMediaDelete>;
  /**
   * Changes ordering of the product media.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productMediaReorder?: Maybe<ProductMediaReorder>;
  /**
   * Updates a product media.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productMediaUpdate?: Maybe<ProductMediaUpdate>;
  /**
   * Reorder product attribute values.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productReorderAttributeValues?: Maybe<ProductReorderAttributeValues>;
  /**
   * Creates/updates translations for a product.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  productTranslate?: Maybe<ProductTranslate>;
  /**
   * Deletes product types.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productTypeBulkDelete?: Maybe<ProductTypeBulkDelete>;
  /**
   * Creates a new product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productTypeCreate?: Maybe<ProductTypeCreate>;
  /**
   * Deletes a product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productTypeDelete?: Maybe<ProductTypeDelete>;
  /**
   * Reorder the attributes of a product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productTypeReorderAttributes?: Maybe<ProductTypeReorderAttributes>;
  /**
   * Updates an existing product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
   */
  productTypeUpdate?: Maybe<ProductTypeUpdate>;
  /**
   * Updates an existing product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productUpdate?: Maybe<ProductUpdate>;
  /**
   * Creates product variants for a given product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantBulkCreate?: Maybe<ProductVariantBulkCreate>;
  /**
   * Deletes product variants.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantBulkDelete?: Maybe<ProductVariantBulkDelete>;
  /**
   * Update multiple product variants.
   *
   * Added in Saleor 3.11.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantBulkUpdate?: Maybe<ProductVariantBulkUpdate>;
  /**
   * Manage product variant prices in channels.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantChannelListingUpdate?: Maybe<ProductVariantChannelListingUpdate>;
  /**
   * Creates a new variant for a product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantCreate?: Maybe<ProductVariantCreate>;
  /**
   * Deletes a product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantDelete?: Maybe<ProductVariantDelete>;
  /**
   * Deactivates product variant preorder. It changes all preorder allocation into regular allocation.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantPreorderDeactivate?: Maybe<ProductVariantPreorderDeactivate>;
  /**
   * Reorder the variants of a product. Mutation updates updated_at on product and triggers PRODUCT_UPDATED webhook.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantReorder?: Maybe<ProductVariantReorder>;
  /**
   * Reorder product variant attribute values.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantReorderAttributeValues?: Maybe<ProductVariantReorderAttributeValues>;
  /**
   * Set default variant for a product. Mutation triggers PRODUCT_UPDATED webhook.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantSetDefault?: Maybe<ProductVariantSetDefault>;
  /**
   * Creates stocks for product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantStocksCreate?: Maybe<ProductVariantStocksCreate>;
  /**
   * Delete stocks from product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantStocksDelete?: Maybe<ProductVariantStocksDelete>;
  /**
   * Update stocks for product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantStocksUpdate?: Maybe<ProductVariantStocksUpdate>;
  /**
   * Creates/updates translations for a product variant.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  productVariantTranslate?: Maybe<ProductVariantTranslate>;
  /**
   * Updates an existing variant for product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  productVariantUpdate?: Maybe<ProductVariantUpdate>;
  /**
   * Request email change of the logged in user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  requestEmailChange?: Maybe<RequestEmailChange>;
  /** Sends an email with the account password modification link. */
  requestPasswordReset?: Maybe<RequestPasswordReset>;
  /**
   * Deletes sales.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleBulkDelete?: Maybe<SaleBulkDelete>;
  /**
   * Adds products, categories, collections to a voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleCataloguesAdd?: Maybe<SaleAddCatalogues>;
  /**
   * Removes products, categories, collections from a sale.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleCataloguesRemove?: Maybe<SaleRemoveCatalogues>;
  /**
   * Manage sale's availability in channels.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleChannelListingUpdate?: Maybe<SaleChannelListingUpdate>;
  /**
   * Creates a new sale.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleCreate?: Maybe<SaleCreate>;
  /**
   * Deletes a sale.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleDelete?: Maybe<SaleDelete>;
  /**
   * Creates/updates translations for a sale.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  saleTranslate?: Maybe<SaleTranslate>;
  /**
   * Updates a sale.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  saleUpdate?: Maybe<SaleUpdate>;
  /** Sets the user's password from the token sent by email using the RequestPasswordReset mutation. */
  setPassword?: Maybe<SetPassword>;
  /**
   * Manage shipping method's availability in channels.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingMethodChannelListingUpdate?: Maybe<ShippingMethodChannelListingUpdate>;
  /**
   * Deletes shipping prices.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceBulkDelete?: Maybe<ShippingPriceBulkDelete>;
  /**
   * Creates a new shipping price.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceCreate?: Maybe<ShippingPriceCreate>;
  /**
   * Deletes a shipping price.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceDelete?: Maybe<ShippingPriceDelete>;
  /**
   * Exclude products from shipping price.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceExcludeProducts?: Maybe<ShippingPriceExcludeProducts>;
  /**
   * Remove product from excluded list for shipping price.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceRemoveProductFromExclude?: Maybe<ShippingPriceRemoveProductFromExclude>;
  /**
   * Creates/updates translations for a shipping method.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  shippingPriceTranslate?: Maybe<ShippingPriceTranslate>;
  /**
   * Updates a new shipping price.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingPriceUpdate?: Maybe<ShippingPriceUpdate>;
  /**
   * Deletes shipping zones.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZoneBulkDelete?: Maybe<ShippingZoneBulkDelete>;
  /**
   * Creates a new shipping zone.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZoneCreate?: Maybe<ShippingZoneCreate>;
  /**
   * Deletes a shipping zone.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZoneDelete?: Maybe<ShippingZoneDelete>;
  /**
   * Updates a new shipping zone.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZoneUpdate?: Maybe<ShippingZoneUpdate>;
  /**
   * Update the shop's address. If the `null` value is passed, the currently selected address will be deleted.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  shopAddressUpdate?: Maybe<ShopAddressUpdate>;
  /**
   * Updates site domain of the shop.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  shopDomainUpdate?: Maybe<ShopDomainUpdate>;
  /**
   * Fetch tax rates.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   * @deprecated
   *
   * DEPRECATED: this mutation will be removed in Saleor 4.0.
   */
  shopFetchTaxRates?: Maybe<ShopFetchTaxRates>;
  /**
   * Creates/updates translations for shop settings.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  shopSettingsTranslate?: Maybe<ShopSettingsTranslate>;
  /**
   * Updates shop settings.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  shopSettingsUpdate?: Maybe<ShopSettingsUpdate>;
  /**
   * Deletes staff users. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  staffBulkDelete?: Maybe<StaffBulkDelete>;
  /**
   * Creates a new staff user. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  staffCreate?: Maybe<StaffCreate>;
  /**
   * Deletes a staff user. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  staffDelete?: Maybe<StaffDelete>;
  /**
   * Creates a new staff notification recipient.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  staffNotificationRecipientCreate?: Maybe<StaffNotificationRecipientCreate>;
  /**
   * Delete staff notification recipient.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  staffNotificationRecipientDelete?: Maybe<StaffNotificationRecipientDelete>;
  /**
   * Updates a staff notification recipient.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  staffNotificationRecipientUpdate?: Maybe<StaffNotificationRecipientUpdate>;
  /**
   * Updates an existing staff user. Apps are not allowed to perform this mutation.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  staffUpdate?: Maybe<StaffUpdate>;
  /**
   * Updates stocks for a given variant and warehouse.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  stockBulkUpdate?: Maybe<StockBulkUpdate>;
  /**
   * Create a tax class.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxClassCreate?: Maybe<TaxClassCreate>;
  /**
   * Delete a tax class. After deleting the tax class any products, product types or shipping methods using it are updated to use the default tax class.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxClassDelete?: Maybe<TaxClassDelete>;
  /**
   * Update a tax class.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxClassUpdate?: Maybe<TaxClassUpdate>;
  /**
   * Update tax configuration for a channel.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxConfigurationUpdate?: Maybe<TaxConfigurationUpdate>;
  /**
   * Remove all tax class rates for a specific country.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxCountryConfigurationDelete?: Maybe<TaxCountryConfigurationDelete>;
  /**
   * Update tax class rates for a specific country.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxCountryConfigurationUpdate?: Maybe<TaxCountryConfigurationUpdate>;
  /**
   * Exempt checkout or order from charging the taxes. When tax exemption is enabled, taxes won't be charged for the checkout or order. Taxes may still be calculated in cases when product prices are entered with the tax included and the net price needs to be known.
   *
   * Added in Saleor 3.8.
   *
   * Requires one of the following permissions: MANAGE_TAXES.
   */
  taxExemptionManage?: Maybe<TaxExemptionManage>;
  /** Create JWT token. */
  tokenCreate?: Maybe<CreateToken>;
  /** Refresh JWT token. Mutation tries to take refreshToken from the input. If it fails it will try to take `refreshToken` from the http-only cookie `refreshToken`. `csrfToken` is required when `refreshToken` is provided as a cookie. */
  tokenRefresh?: Maybe<RefreshToken>;
  /** Verify JWT token. */
  tokenVerify?: Maybe<VerifyToken>;
  /**
   * Deactivate all JWT tokens of the currently authenticated user.
   *
   * Requires one of the following permissions: AUTHENTICATED_USER.
   */
  tokensDeactivateAll?: Maybe<DeactivateAllUserTokens>;
  /**
   * Create transaction for checkout or order.
   *
   * Added in Saleor 3.4.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: HANDLE_PAYMENTS.
   */
  transactionCreate?: Maybe<TransactionCreate>;
  /**
   * Report the event for the transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires the following permissions: OWNER and HANDLE_PAYMENTS for apps, HANDLE_PAYMENTS for staff users. Staff user cannot update a transaction that is owned by the app.
   */
  transactionEventReport?: Maybe<TransactionEventReport>;
  /**
   * Initializes a transaction session. It triggers the webhook `TRANSACTION_INITIALIZE_SESSION`, to the requested `paymentGateways`.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  transactionInitialize?: Maybe<TransactionInitialize>;
  /**
   * Processes a transaction session. It triggers the webhook `TRANSACTION_PROCESS_SESSION`, to the assigned `paymentGateways`.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  transactionProcess?: Maybe<TransactionProcess>;
  /**
   * Request an action for payment transaction.
   *
   * Added in Saleor 3.4.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: HANDLE_PAYMENTS.
   */
  transactionRequestAction?: Maybe<TransactionRequestAction>;
  /**
   * Update transaction.
   *
   * Added in Saleor 3.4.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires the following permissions: OWNER and HANDLE_PAYMENTS for apps, HANDLE_PAYMENTS for staff users. Staff user cannot update a transaction that is owned by the app.
   */
  transactionUpdate?: Maybe<TransactionUpdate>;
  /**
   * Remove shipping zone from given warehouse.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  unassignWarehouseShippingZone?: Maybe<WarehouseShippingZoneUnassign>;
  /** Updates metadata of an object. To use it, you need to have access to the modified object. */
  updateMetadata?: Maybe<UpdateMetadata>;
  /** Updates private metadata of an object. To use it, you need to be an authenticated staff user or an app and have access to the modified object. */
  updatePrivateMetadata?: Maybe<UpdatePrivateMetadata>;
  /**
   * Updates given warehouse.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  updateWarehouse?: Maybe<WarehouseUpdate>;
  /**
   * Deletes a user avatar. Only for staff members.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
   */
  userAvatarDelete?: Maybe<UserAvatarDelete>;
  /**
   * Create a user avatar. Only for staff members. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
   */
  userAvatarUpdate?: Maybe<UserAvatarUpdate>;
  /**
   * Activate or deactivate users.
   *
   * Requires one of the following permissions: MANAGE_USERS.
   */
  userBulkSetActive?: Maybe<UserBulkSetActive>;
  /**
   * Assign an media to a product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  variantMediaAssign?: Maybe<VariantMediaAssign>;
  /**
   * Unassign an media from a product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  variantMediaUnassign?: Maybe<VariantMediaUnassign>;
  /**
   * Deletes vouchers.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherBulkDelete?: Maybe<VoucherBulkDelete>;
  /**
   * Adds products, categories, collections to a voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherCataloguesAdd?: Maybe<VoucherAddCatalogues>;
  /**
   * Removes products, categories, collections from a voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherCataloguesRemove?: Maybe<VoucherRemoveCatalogues>;
  /**
   * Manage voucher's availability in channels.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherChannelListingUpdate?: Maybe<VoucherChannelListingUpdate>;
  /**
   * Creates a new voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherCreate?: Maybe<VoucherCreate>;
  /**
   * Deletes a voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherDelete?: Maybe<VoucherDelete>;
  /**
   * Creates/updates translations for a voucher.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  voucherTranslate?: Maybe<VoucherTranslate>;
  /**
   * Updates a voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucherUpdate?: Maybe<VoucherUpdate>;
  /**
   * Creates a new webhook subscription.
   *
   * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
   */
  webhookCreate?: Maybe<WebhookCreate>;
  /**
   * Delete a webhook. Before the deletion, the webhook is deactivated to pause any deliveries that are already scheduled. The deletion might fail if delivery is in progress. In such a case, the webhook is not deleted but remains deactivated.
   *
   * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
   */
  webhookDelete?: Maybe<WebhookDelete>;
  /**
   * Performs a dry run of a webhook event. Supports a single event (the first, if multiple provided in the `query`). Requires permission relevant to processed event.
   *
   * Added in Saleor 3.11.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
   */
  webhookDryRun?: Maybe<WebhookDryRun>;
  /**
   * Trigger a webhook event. Supports a single event (the first, if multiple provided in the `webhook.subscription_query`). Requires permission relevant to processed event. Successfully delivered webhook returns `delivery` with status='PENDING' and empty payload.
   *
   * Added in Saleor 3.11.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
   */
  webhookTrigger?: Maybe<WebhookTrigger>;
  /**
   * Updates a webhook subscription.
   *
   * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
   */
  webhookUpdate?: Maybe<WebhookUpdate>;
};


export type MutationAccountAddressCreateArgs = {
  input: AddressInput;
  type?: InputMaybe<AddressTypeEnum>;
};


export type MutationAccountAddressDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAccountAddressUpdateArgs = {
  id: Scalars['ID']['input'];
  input: AddressInput;
};


export type MutationAccountDeleteArgs = {
  token: Scalars['String']['input'];
};


export type MutationAccountRegisterArgs = {
  input: AccountRegisterInput;
};


export type MutationAccountRequestDeletionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  redirectUrl: Scalars['String']['input'];
};


export type MutationAccountSetDefaultAddressArgs = {
  id: Scalars['ID']['input'];
  type: AddressTypeEnum;
};


export type MutationAccountUpdateArgs = {
  input: AccountInput;
};


export type MutationAddressCreateArgs = {
  input: AddressInput;
  userId: Scalars['ID']['input'];
};


export type MutationAddressDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAddressSetDefaultArgs = {
  addressId: Scalars['ID']['input'];
  type: AddressTypeEnum;
  userId: Scalars['ID']['input'];
};


export type MutationAddressUpdateArgs = {
  id: Scalars['ID']['input'];
  input: AddressInput;
};


export type MutationAppActivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAppCreateArgs = {
  input: AppInput;
};


export type MutationAppDeactivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAppDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAppDeleteFailedInstallationArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAppFetchManifestArgs = {
  manifestUrl: Scalars['String']['input'];
};


export type MutationAppInstallArgs = {
  input: AppInstallInput;
};


export type MutationAppRetryInstallArgs = {
  activateAfterInstallation?: InputMaybe<Scalars['Boolean']['input']>;
  id: Scalars['ID']['input'];
};


export type MutationAppTokenCreateArgs = {
  input: AppTokenInput;
};


export type MutationAppTokenDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationAppTokenVerifyArgs = {
  token: Scalars['String']['input'];
};


export type MutationAppUpdateArgs = {
  id: Scalars['ID']['input'];
  input: AppInput;
};


export type MutationAssignNavigationArgs = {
  menu?: InputMaybe<Scalars['ID']['input']>;
  navigationType: NavigationType;
};


export type MutationAssignWarehouseShippingZoneArgs = {
  id: Scalars['ID']['input'];
  shippingZoneIds: Array<Scalars['ID']['input']>;
};


export type MutationAttributeBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationAttributeCreateArgs = {
  input: AttributeCreateInput;
};


export type MutationAttributeDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationAttributeReorderValuesArgs = {
  attributeId: Scalars['ID']['input'];
  moves: Array<ReorderInput>;
};


export type MutationAttributeTranslateArgs = {
  id: Scalars['ID']['input'];
  input: NameTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationAttributeUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: AttributeUpdateInput;
};


export type MutationAttributeValueBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationAttributeValueCreateArgs = {
  attribute: Scalars['ID']['input'];
  input: AttributeValueCreateInput;
};


export type MutationAttributeValueDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationAttributeValueTranslateArgs = {
  id: Scalars['ID']['input'];
  input: AttributeValueTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationAttributeValueUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: AttributeValueUpdateInput;
};


export type MutationCategoryBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationCategoryCreateArgs = {
  input: CategoryInput;
  parent?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationCategoryDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCategoryTranslateArgs = {
  id: Scalars['ID']['input'];
  input: TranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationCategoryUpdateArgs = {
  id: Scalars['ID']['input'];
  input: CategoryInput;
};


export type MutationChannelActivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationChannelCreateArgs = {
  input: ChannelCreateInput;
};


export type MutationChannelDeactivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationChannelDeleteArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<ChannelDeleteInput>;
};


export type MutationChannelReorderWarehousesArgs = {
  channelId: Scalars['ID']['input'];
  moves: Array<ReorderInput>;
};


export type MutationChannelUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ChannelUpdateInput;
};


export type MutationCheckoutAddPromoCodeArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  promoCode: Scalars['String']['input'];
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutBillingAddressUpdateArgs = {
  billingAddress: AddressInput;
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
  validationRules?: InputMaybe<CheckoutAddressValidationRules>;
};


export type MutationCheckoutCompleteArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  metadata?: InputMaybe<Array<MetadataInput>>;
  paymentData?: InputMaybe<Scalars['JSONString']['input']>;
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
  storeSource?: InputMaybe<Scalars['Boolean']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutCreateArgs = {
  input: CheckoutCreateInput;
};


export type MutationCheckoutCreateFromOrderArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCheckoutCustomerAttachArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  customerId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutCustomerDetachArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutDeliveryMethodUpdateArgs = {
  deliveryMethodId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutEmailUpdateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  email: Scalars['String']['input'];
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutLanguageCodeUpdateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  languageCode: LanguageCodeEnum;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutLineDeleteArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  lineId?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutLinesAddArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  lines: Array<CheckoutLineInput>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutLinesDeleteArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  linesIds: Array<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutLinesUpdateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  lines: Array<CheckoutLineUpdateInput>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutPaymentCreateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: PaymentInput;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutRemovePromoCodeArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  promoCode?: InputMaybe<Scalars['String']['input']>;
  promoCodeId?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCheckoutShippingAddressUpdateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  shippingAddress: AddressInput;
  token?: InputMaybe<Scalars['UUID']['input']>;
  validationRules?: InputMaybe<CheckoutAddressValidationRules>;
};


export type MutationCheckoutShippingMethodUpdateArgs = {
  checkoutId?: InputMaybe<Scalars['ID']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  shippingMethodId: Scalars['ID']['input'];
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type MutationCollectionAddProductsArgs = {
  collectionId: Scalars['ID']['input'];
  products: Array<Scalars['ID']['input']>;
};


export type MutationCollectionBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationCollectionChannelListingUpdateArgs = {
  id: Scalars['ID']['input'];
  input: CollectionChannelListingUpdateInput;
};


export type MutationCollectionCreateArgs = {
  input: CollectionCreateInput;
};


export type MutationCollectionDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCollectionRemoveProductsArgs = {
  collectionId: Scalars['ID']['input'];
  products: Array<Scalars['ID']['input']>;
};


export type MutationCollectionReorderProductsArgs = {
  collectionId: Scalars['ID']['input'];
  moves: Array<MoveProductInput>;
};


export type MutationCollectionTranslateArgs = {
  id: Scalars['ID']['input'];
  input: TranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationCollectionUpdateArgs = {
  id: Scalars['ID']['input'];
  input: CollectionInput;
};


export type MutationConfirmAccountArgs = {
  email: Scalars['String']['input'];
  token: Scalars['String']['input'];
};


export type MutationConfirmEmailChangeArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  token: Scalars['String']['input'];
};


export type MutationCreateWarehouseArgs = {
  input: WarehouseCreateInput;
};


export type MutationCustomerBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationCustomerBulkUpdateArgs = {
  customers: Array<CustomerBulkUpdateInput>;
  errorPolicy?: InputMaybe<ErrorPolicyEnum>;
};


export type MutationCustomerCreateArgs = {
  input: UserCreateInput;
};


export type MutationCustomerDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationCustomerUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: CustomerInput;
};


export type MutationDeleteMetadataArgs = {
  id: Scalars['ID']['input'];
  keys: Array<Scalars['String']['input']>;
};


export type MutationDeletePrivateMetadataArgs = {
  id: Scalars['ID']['input'];
  keys: Array<Scalars['String']['input']>;
};


export type MutationDeleteWarehouseArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDigitalContentCreateArgs = {
  input: DigitalContentUploadInput;
  variantId: Scalars['ID']['input'];
};


export type MutationDigitalContentDeleteArgs = {
  variantId: Scalars['ID']['input'];
};


export type MutationDigitalContentUpdateArgs = {
  input: DigitalContentInput;
  variantId: Scalars['ID']['input'];
};


export type MutationDigitalContentUrlCreateArgs = {
  input: DigitalContentUrlCreateInput;
};


export type MutationDraftOrderBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationDraftOrderCompleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDraftOrderCreateArgs = {
  input: DraftOrderCreateInput;
};


export type MutationDraftOrderDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationDraftOrderLinesBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationDraftOrderUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: DraftOrderInput;
};


export type MutationEventDeliveryRetryArgs = {
  id: Scalars['ID']['input'];
};


export type MutationExportGiftCardsArgs = {
  input: ExportGiftCardsInput;
};


export type MutationExportProductsArgs = {
  input: ExportProductsInput;
};


export type MutationExternalAuthenticationUrlArgs = {
  input: Scalars['JSONString']['input'];
  pluginId: Scalars['String']['input'];
};


export type MutationExternalLogoutArgs = {
  input: Scalars['JSONString']['input'];
  pluginId: Scalars['String']['input'];
};


export type MutationExternalNotificationTriggerArgs = {
  channel: Scalars['String']['input'];
  input: ExternalNotificationTriggerInput;
  pluginId?: InputMaybe<Scalars['String']['input']>;
};


export type MutationExternalObtainAccessTokensArgs = {
  input: Scalars['JSONString']['input'];
  pluginId: Scalars['String']['input'];
};


export type MutationExternalRefreshArgs = {
  input: Scalars['JSONString']['input'];
  pluginId: Scalars['String']['input'];
};


export type MutationExternalVerifyArgs = {
  input: Scalars['JSONString']['input'];
  pluginId: Scalars['String']['input'];
};


export type MutationFileUploadArgs = {
  file: Scalars['Upload']['input'];
};


export type MutationGiftCardActivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationGiftCardAddNoteArgs = {
  id: Scalars['ID']['input'];
  input: GiftCardAddNoteInput;
};


export type MutationGiftCardBulkActivateArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationGiftCardBulkCreateArgs = {
  input: GiftCardBulkCreateInput;
};


export type MutationGiftCardBulkDeactivateArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationGiftCardBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationGiftCardCreateArgs = {
  input: GiftCardCreateInput;
};


export type MutationGiftCardDeactivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationGiftCardDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationGiftCardResendArgs = {
  input: GiftCardResendInput;
};


export type MutationGiftCardSettingsUpdateArgs = {
  input: GiftCardSettingsUpdateInput;
};


export type MutationGiftCardUpdateArgs = {
  id: Scalars['ID']['input'];
  input: GiftCardUpdateInput;
};


export type MutationInvoiceCreateArgs = {
  input: InvoiceCreateInput;
  orderId: Scalars['ID']['input'];
};


export type MutationInvoiceDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationInvoiceRequestArgs = {
  number?: InputMaybe<Scalars['String']['input']>;
  orderId: Scalars['ID']['input'];
};


export type MutationInvoiceRequestDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationInvoiceSendNotificationArgs = {
  id: Scalars['ID']['input'];
};


export type MutationInvoiceUpdateArgs = {
  id: Scalars['ID']['input'];
  input: UpdateInvoiceInput;
};


export type MutationMenuBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationMenuCreateArgs = {
  input: MenuCreateInput;
};


export type MutationMenuDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationMenuItemBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationMenuItemCreateArgs = {
  input: MenuItemCreateInput;
};


export type MutationMenuItemDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationMenuItemMoveArgs = {
  menu: Scalars['ID']['input'];
  moves: Array<MenuItemMoveInput>;
};


export type MutationMenuItemTranslateArgs = {
  id: Scalars['ID']['input'];
  input: NameTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationMenuItemUpdateArgs = {
  id: Scalars['ID']['input'];
  input: MenuItemInput;
};


export type MutationMenuUpdateArgs = {
  id: Scalars['ID']['input'];
  input: MenuInput;
};


export type MutationOrderAddNoteArgs = {
  input: OrderAddNoteInput;
  order: Scalars['ID']['input'];
};


export type MutationOrderBulkCancelArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationOrderCancelArgs = {
  id: Scalars['ID']['input'];
};


export type MutationOrderCaptureArgs = {
  amount: Scalars['PositiveDecimal']['input'];
  id: Scalars['ID']['input'];
};


export type MutationOrderConfirmArgs = {
  id: Scalars['ID']['input'];
};


export type MutationOrderCreateFromCheckoutArgs = {
  id: Scalars['ID']['input'];
  metadata?: InputMaybe<Array<MetadataInput>>;
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  removeCheckout?: InputMaybe<Scalars['Boolean']['input']>;
};


export type MutationOrderDiscountAddArgs = {
  input: OrderDiscountCommonInput;
  orderId: Scalars['ID']['input'];
};


export type MutationOrderDiscountDeleteArgs = {
  discountId: Scalars['ID']['input'];
};


export type MutationOrderDiscountUpdateArgs = {
  discountId: Scalars['ID']['input'];
  input: OrderDiscountCommonInput;
};


export type MutationOrderFulfillArgs = {
  input: OrderFulfillInput;
  order?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationOrderFulfillmentApproveArgs = {
  allowStockToBeExceeded?: InputMaybe<Scalars['Boolean']['input']>;
  id: Scalars['ID']['input'];
  notifyCustomer: Scalars['Boolean']['input'];
};


export type MutationOrderFulfillmentCancelArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<FulfillmentCancelInput>;
};


export type MutationOrderFulfillmentRefundProductsArgs = {
  input: OrderRefundProductsInput;
  order: Scalars['ID']['input'];
};


export type MutationOrderFulfillmentReturnProductsArgs = {
  input: OrderReturnProductsInput;
  order: Scalars['ID']['input'];
};


export type MutationOrderFulfillmentUpdateTrackingArgs = {
  id: Scalars['ID']['input'];
  input: FulfillmentUpdateTrackingInput;
};


export type MutationOrderGrantRefundCreateArgs = {
  id: Scalars['ID']['input'];
  input: OrderGrantRefundCreateInput;
};


export type MutationOrderGrantRefundUpdateArgs = {
  id: Scalars['ID']['input'];
  input: OrderGrantRefundUpdateInput;
};


export type MutationOrderLineDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationOrderLineDiscountRemoveArgs = {
  orderLineId: Scalars['ID']['input'];
};


export type MutationOrderLineDiscountUpdateArgs = {
  input: OrderDiscountCommonInput;
  orderLineId: Scalars['ID']['input'];
};


export type MutationOrderLineUpdateArgs = {
  id: Scalars['ID']['input'];
  input: OrderLineInput;
};


export type MutationOrderLinesCreateArgs = {
  id: Scalars['ID']['input'];
  input: Array<OrderLineCreateInput>;
};


export type MutationOrderMarkAsPaidArgs = {
  id: Scalars['ID']['input'];
  transactionReference?: InputMaybe<Scalars['String']['input']>;
};


export type MutationOrderRefundArgs = {
  amount: Scalars['PositiveDecimal']['input'];
  id: Scalars['ID']['input'];
};


export type MutationOrderSettingsUpdateArgs = {
  input: OrderSettingsUpdateInput;
};


export type MutationOrderUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: OrderUpdateInput;
};


export type MutationOrderUpdateShippingArgs = {
  input: OrderUpdateShippingInput;
  order: Scalars['ID']['input'];
};


export type MutationOrderVoidArgs = {
  id: Scalars['ID']['input'];
};


export type MutationPageAttributeAssignArgs = {
  attributeIds: Array<Scalars['ID']['input']>;
  pageTypeId: Scalars['ID']['input'];
};


export type MutationPageAttributeUnassignArgs = {
  attributeIds: Array<Scalars['ID']['input']>;
  pageTypeId: Scalars['ID']['input'];
};


export type MutationPageBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationPageBulkPublishArgs = {
  ids: Array<Scalars['ID']['input']>;
  isPublished: Scalars['Boolean']['input'];
};


export type MutationPageCreateArgs = {
  input: PageCreateInput;
};


export type MutationPageDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationPageReorderAttributeValuesArgs = {
  attributeId: Scalars['ID']['input'];
  moves: Array<ReorderInput>;
  pageId: Scalars['ID']['input'];
};


export type MutationPageTranslateArgs = {
  id: Scalars['ID']['input'];
  input: PageTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationPageTypeBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationPageTypeCreateArgs = {
  input: PageTypeCreateInput;
};


export type MutationPageTypeDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationPageTypeReorderAttributesArgs = {
  moves: Array<ReorderInput>;
  pageTypeId: Scalars['ID']['input'];
};


export type MutationPageTypeUpdateArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  input: PageTypeUpdateInput;
};


export type MutationPageUpdateArgs = {
  id: Scalars['ID']['input'];
  input: PageInput;
};


export type MutationPasswordChangeArgs = {
  newPassword: Scalars['String']['input'];
  oldPassword?: InputMaybe<Scalars['String']['input']>;
};


export type MutationPaymentCaptureArgs = {
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  paymentId: Scalars['ID']['input'];
};


export type MutationPaymentCheckBalanceArgs = {
  input: PaymentCheckBalanceInput;
};


export type MutationPaymentGatewayInitializeArgs = {
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  id: Scalars['ID']['input'];
  paymentGateways?: InputMaybe<Array<PaymentGatewayToInitialize>>;
};


export type MutationPaymentInitializeArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  gateway: Scalars['String']['input'];
  paymentData?: InputMaybe<Scalars['JSONString']['input']>;
};


export type MutationPaymentRefundArgs = {
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  paymentId: Scalars['ID']['input'];
};


export type MutationPaymentVoidArgs = {
  paymentId: Scalars['ID']['input'];
};


export type MutationPermissionGroupCreateArgs = {
  input: PermissionGroupCreateInput;
};


export type MutationPermissionGroupDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationPermissionGroupUpdateArgs = {
  id: Scalars['ID']['input'];
  input: PermissionGroupUpdateInput;
};


export type MutationPluginUpdateArgs = {
  channelId?: InputMaybe<Scalars['ID']['input']>;
  id: Scalars['ID']['input'];
  input: PluginUpdateInput;
};


export type MutationProductAttributeAssignArgs = {
  operations: Array<ProductAttributeAssignInput>;
  productTypeId: Scalars['ID']['input'];
};


export type MutationProductAttributeAssignmentUpdateArgs = {
  operations: Array<ProductAttributeAssignmentUpdateInput>;
  productTypeId: Scalars['ID']['input'];
};


export type MutationProductAttributeUnassignArgs = {
  attributeIds: Array<Scalars['ID']['input']>;
  productTypeId: Scalars['ID']['input'];
};


export type MutationProductBulkCreateArgs = {
  errorPolicy?: InputMaybe<ErrorPolicyEnum>;
  products: Array<ProductBulkCreateInput>;
};


export type MutationProductBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationProductChannelListingUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ProductChannelListingUpdateInput;
};


export type MutationProductCreateArgs = {
  input: ProductCreateInput;
};


export type MutationProductDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationProductMediaBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationProductMediaCreateArgs = {
  input: ProductMediaCreateInput;
};


export type MutationProductMediaDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationProductMediaReorderArgs = {
  mediaIds: Array<Scalars['ID']['input']>;
  productId: Scalars['ID']['input'];
};


export type MutationProductMediaUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ProductMediaUpdateInput;
};


export type MutationProductReorderAttributeValuesArgs = {
  attributeId: Scalars['ID']['input'];
  moves: Array<ReorderInput>;
  productId: Scalars['ID']['input'];
};


export type MutationProductTranslateArgs = {
  id: Scalars['ID']['input'];
  input: TranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationProductTypeBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationProductTypeCreateArgs = {
  input: ProductTypeInput;
};


export type MutationProductTypeDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationProductTypeReorderAttributesArgs = {
  moves: Array<ReorderInput>;
  productTypeId: Scalars['ID']['input'];
  type: ProductAttributeType;
};


export type MutationProductTypeUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ProductTypeInput;
};


export type MutationProductUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: ProductInput;
};


export type MutationProductVariantBulkCreateArgs = {
  errorPolicy?: InputMaybe<ErrorPolicyEnum>;
  product: Scalars['ID']['input'];
  variants: Array<ProductVariantBulkCreateInput>;
};


export type MutationProductVariantBulkDeleteArgs = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  skus?: InputMaybe<Array<Scalars['String']['input']>>;
};


export type MutationProductVariantBulkUpdateArgs = {
  errorPolicy?: InputMaybe<ErrorPolicyEnum>;
  product: Scalars['ID']['input'];
  variants: Array<ProductVariantBulkUpdateInput>;
};


export type MutationProductVariantChannelListingUpdateArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  input: Array<ProductVariantChannelListingAddInput>;
  sku?: InputMaybe<Scalars['String']['input']>;
};


export type MutationProductVariantCreateArgs = {
  input: ProductVariantCreateInput;
};


export type MutationProductVariantDeleteArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
};


export type MutationProductVariantPreorderDeactivateArgs = {
  id: Scalars['ID']['input'];
};


export type MutationProductVariantReorderArgs = {
  moves: Array<ReorderInput>;
  productId: Scalars['ID']['input'];
};


export type MutationProductVariantReorderAttributeValuesArgs = {
  attributeId: Scalars['ID']['input'];
  moves: Array<ReorderInput>;
  variantId: Scalars['ID']['input'];
};


export type MutationProductVariantSetDefaultArgs = {
  productId: Scalars['ID']['input'];
  variantId: Scalars['ID']['input'];
};


export type MutationProductVariantStocksCreateArgs = {
  stocks: Array<StockInput>;
  variantId: Scalars['ID']['input'];
};


export type MutationProductVariantStocksDeleteArgs = {
  sku?: InputMaybe<Scalars['String']['input']>;
  variantId?: InputMaybe<Scalars['ID']['input']>;
  warehouseIds?: InputMaybe<Array<Scalars['ID']['input']>>;
};


export type MutationProductVariantStocksUpdateArgs = {
  sku?: InputMaybe<Scalars['String']['input']>;
  stocks: Array<StockInput>;
  variantId?: InputMaybe<Scalars['ID']['input']>;
};


export type MutationProductVariantTranslateArgs = {
  id: Scalars['ID']['input'];
  input: NameTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationProductVariantUpdateArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  input: ProductVariantInput;
  sku?: InputMaybe<Scalars['String']['input']>;
};


export type MutationRequestEmailChangeArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  newEmail: Scalars['String']['input'];
  password: Scalars['String']['input'];
  redirectUrl: Scalars['String']['input'];
};


export type MutationRequestPasswordResetArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  email: Scalars['String']['input'];
  redirectUrl: Scalars['String']['input'];
};


export type MutationSaleBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationSaleCataloguesAddArgs = {
  id: Scalars['ID']['input'];
  input: CatalogueInput;
};


export type MutationSaleCataloguesRemoveArgs = {
  id: Scalars['ID']['input'];
  input: CatalogueInput;
};


export type MutationSaleChannelListingUpdateArgs = {
  id: Scalars['ID']['input'];
  input: SaleChannelListingInput;
};


export type MutationSaleCreateArgs = {
  input: SaleInput;
};


export type MutationSaleDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationSaleTranslateArgs = {
  id: Scalars['ID']['input'];
  input: NameTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationSaleUpdateArgs = {
  id: Scalars['ID']['input'];
  input: SaleInput;
};


export type MutationSetPasswordArgs = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
  token: Scalars['String']['input'];
};


export type MutationShippingMethodChannelListingUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ShippingMethodChannelListingInput;
};


export type MutationShippingPriceBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationShippingPriceCreateArgs = {
  input: ShippingPriceInput;
};


export type MutationShippingPriceDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationShippingPriceExcludeProductsArgs = {
  id: Scalars['ID']['input'];
  input: ShippingPriceExcludeProductsInput;
};


export type MutationShippingPriceRemoveProductFromExcludeArgs = {
  id: Scalars['ID']['input'];
  products: Array<Scalars['ID']['input']>;
};


export type MutationShippingPriceTranslateArgs = {
  id: Scalars['ID']['input'];
  input: ShippingPriceTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationShippingPriceUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ShippingPriceInput;
};


export type MutationShippingZoneBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationShippingZoneCreateArgs = {
  input: ShippingZoneCreateInput;
};


export type MutationShippingZoneDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationShippingZoneUpdateArgs = {
  id: Scalars['ID']['input'];
  input: ShippingZoneUpdateInput;
};


export type MutationShopAddressUpdateArgs = {
  input?: InputMaybe<AddressInput>;
};


export type MutationShopDomainUpdateArgs = {
  input?: InputMaybe<SiteDomainInput>;
};


export type MutationShopSettingsTranslateArgs = {
  input: ShopSettingsTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationShopSettingsUpdateArgs = {
  input: ShopSettingsInput;
};


export type MutationStaffBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationStaffCreateArgs = {
  input: StaffCreateInput;
};


export type MutationStaffDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationStaffNotificationRecipientCreateArgs = {
  input: StaffNotificationRecipientInput;
};


export type MutationStaffNotificationRecipientDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationStaffNotificationRecipientUpdateArgs = {
  id: Scalars['ID']['input'];
  input: StaffNotificationRecipientInput;
};


export type MutationStaffUpdateArgs = {
  id: Scalars['ID']['input'];
  input: StaffUpdateInput;
};


export type MutationStockBulkUpdateArgs = {
  errorPolicy?: InputMaybe<ErrorPolicyEnum>;
  stocks: Array<StockBulkUpdateInput>;
};


export type MutationTaxClassCreateArgs = {
  input: TaxClassCreateInput;
};


export type MutationTaxClassDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationTaxClassUpdateArgs = {
  id: Scalars['ID']['input'];
  input: TaxClassUpdateInput;
};


export type MutationTaxConfigurationUpdateArgs = {
  id: Scalars['ID']['input'];
  input: TaxConfigurationUpdateInput;
};


export type MutationTaxCountryConfigurationDeleteArgs = {
  countryCode: CountryCode;
};


export type MutationTaxCountryConfigurationUpdateArgs = {
  countryCode: CountryCode;
  updateTaxClassRates: Array<TaxClassRateInput>;
};


export type MutationTaxExemptionManageArgs = {
  id: Scalars['ID']['input'];
  taxExemption: Scalars['Boolean']['input'];
};


export type MutationTokenCreateArgs = {
  audience?: InputMaybe<Scalars['String']['input']>;
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};


export type MutationTokenRefreshArgs = {
  csrfToken?: InputMaybe<Scalars['String']['input']>;
  refreshToken?: InputMaybe<Scalars['String']['input']>;
};


export type MutationTokenVerifyArgs = {
  token: Scalars['String']['input'];
};


export type MutationTransactionCreateArgs = {
  id: Scalars['ID']['input'];
  transaction: TransactionCreateInput;
  transactionEvent?: InputMaybe<TransactionEventInput>;
};


export type MutationTransactionEventReportArgs = {
  amount: Scalars['PositiveDecimal']['input'];
  availableActions?: InputMaybe<Array<TransactionActionEnum>>;
  externalUrl?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
  message?: InputMaybe<Scalars['String']['input']>;
  pspReference: Scalars['String']['input'];
  time?: InputMaybe<Scalars['DateTime']['input']>;
  type: TransactionEventTypeEnum;
};


export type MutationTransactionInitializeArgs = {
  action?: InputMaybe<TransactionFlowStrategyEnum>;
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  id: Scalars['ID']['input'];
  paymentGateway: PaymentGatewayToInitialize;
};


export type MutationTransactionProcessArgs = {
  data?: InputMaybe<Scalars['JSON']['input']>;
  id: Scalars['ID']['input'];
};


export type MutationTransactionRequestActionArgs = {
  actionType: TransactionActionEnum;
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  id: Scalars['ID']['input'];
};


export type MutationTransactionUpdateArgs = {
  id: Scalars['ID']['input'];
  transaction?: InputMaybe<TransactionUpdateInput>;
  transactionEvent?: InputMaybe<TransactionEventInput>;
};


export type MutationUnassignWarehouseShippingZoneArgs = {
  id: Scalars['ID']['input'];
  shippingZoneIds: Array<Scalars['ID']['input']>;
};


export type MutationUpdateMetadataArgs = {
  id: Scalars['ID']['input'];
  input: Array<MetadataInput>;
};


export type MutationUpdatePrivateMetadataArgs = {
  id: Scalars['ID']['input'];
  input: Array<MetadataInput>;
};


export type MutationUpdateWarehouseArgs = {
  id: Scalars['ID']['input'];
  input: WarehouseUpdateInput;
};


export type MutationUserAvatarUpdateArgs = {
  image: Scalars['Upload']['input'];
};


export type MutationUserBulkSetActiveArgs = {
  ids: Array<Scalars['ID']['input']>;
  isActive: Scalars['Boolean']['input'];
};


export type MutationVariantMediaAssignArgs = {
  mediaId: Scalars['ID']['input'];
  variantId: Scalars['ID']['input'];
};


export type MutationVariantMediaUnassignArgs = {
  mediaId: Scalars['ID']['input'];
  variantId: Scalars['ID']['input'];
};


export type MutationVoucherBulkDeleteArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationVoucherCataloguesAddArgs = {
  id: Scalars['ID']['input'];
  input: CatalogueInput;
};


export type MutationVoucherCataloguesRemoveArgs = {
  id: Scalars['ID']['input'];
  input: CatalogueInput;
};


export type MutationVoucherChannelListingUpdateArgs = {
  id: Scalars['ID']['input'];
  input: VoucherChannelListingInput;
};


export type MutationVoucherCreateArgs = {
  input: VoucherInput;
};


export type MutationVoucherDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationVoucherTranslateArgs = {
  id: Scalars['ID']['input'];
  input: NameTranslationInput;
  languageCode: LanguageCodeEnum;
};


export type MutationVoucherUpdateArgs = {
  id: Scalars['ID']['input'];
  input: VoucherInput;
};


export type MutationWebhookCreateArgs = {
  input: WebhookCreateInput;
};


export type MutationWebhookDeleteArgs = {
  id: Scalars['ID']['input'];
};


export type MutationWebhookDryRunArgs = {
  objectId: Scalars['ID']['input'];
  query: Scalars['String']['input'];
};


export type MutationWebhookTriggerArgs = {
  objectId: Scalars['ID']['input'];
  webhookId: Scalars['ID']['input'];
};


export type MutationWebhookUpdateArgs = {
  id: Scalars['ID']['input'];
  input: WebhookUpdateInput;
};

export type NameTranslationInput = {
  name?: InputMaybe<Scalars['String']['input']>;
};

export enum NavigationType {
  /** Main storefront navigation. */
  Main = 'MAIN',
  /** Secondary storefront navigation. */
  Secondary = 'SECONDARY'
}

/** An object with an ID */
export type Node = {
  /** The ID of the object. */
  id: Scalars['ID']['output'];
};

export type ObjectWithMetadata = {
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /** Public metadata. Use `keys` to control which fields you want to include. The default is to include everything. */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /** Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything. */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
};


export type ObjectWithMetadataMetafieldArgs = {
  key: Scalars['String']['input'];
};


export type ObjectWithMetadataMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


export type ObjectWithMetadataPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


export type ObjectWithMetadataPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/** Represents an order in the shop. */
export type Order = Node & ObjectWithMetadata & {
  __typename?: 'Order';
  /** List of actions that can be performed in the current state of an order. */
  actions: Array<OrderAction>;
  /**
   * The authorize status of the order.
   *
   * Added in Saleor 3.4.
   */
  authorizeStatus: OrderAuthorizeStatusEnum;
  /**
   * Collection points that can be used for this order.
   *
   * Added in Saleor 3.1.
   */
  availableCollectionPoints: Array<Warehouse>;
  /**
   * Shipping methods that can be used with this order.
   * @deprecated Use `shippingMethods`, this field will be removed in 4.0
   */
  availableShippingMethods?: Maybe<Array<ShippingMethod>>;
  /** Billing address. The full data can be access for orders created in Saleor 3.2 and later, for other orders requires one of the following permissions: MANAGE_ORDERS, OWNER. */
  billingAddress?: Maybe<Address>;
  /** Informs whether a draft order can be finalized(turned into a regular order). */
  canFinalize: Scalars['Boolean']['output'];
  channel: Channel;
  /**
   * The charge status of the order.
   *
   * Added in Saleor 3.4.
   */
  chargeStatus: OrderChargeStatusEnum;
  /**
   * ID of the checkout that the order was created from.
   *
   * Added in Saleor 3.11.
   */
  checkoutId?: Maybe<Scalars['ID']['output']>;
  collectionPointName?: Maybe<Scalars['String']['output']>;
  created: Scalars['DateTime']['output'];
  customerNote: Scalars['String']['output'];
  /**
   * The delivery method selected for this order.
   *
   * Added in Saleor 3.1.
   */
  deliveryMethod?: Maybe<DeliveryMethod>;
  /**
   * Returns applied discount.
   * @deprecated This field will be removed in Saleor 4.0. Use the `discounts` field instead.
   */
  discount?: Maybe<Money>;
  /**
   * Discount name.
   * @deprecated This field will be removed in Saleor 4.0. Use the `discounts` field instead.
   */
  discountName?: Maybe<Scalars['String']['output']>;
  /** List of all discounts assigned to the order. */
  discounts: Array<OrderDiscount>;
  /**
   * Determines whether checkout prices should include taxes when displayed in a storefront.
   *
   * Added in Saleor 3.9.
   */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** List of errors that occurred during order validation. */
  errors: Array<OrderError>;
  /**
   * List of events associated with the order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  events: Array<OrderEvent>;
  /**
   * External ID of this order.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  /** List of shipments for the order. */
  fulfillments: Array<Fulfillment>;
  /** List of user gift cards. */
  giftCards: Array<GiftCard>;
  /**
   * List of granted refunds.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  grantedRefunds: Array<OrderGrantedRefund>;
  id: Scalars['ID']['output'];
  /** List of order invoices. Can be fetched for orders created in Saleor 3.2 and later, for other orders requires one of the following permissions: MANAGE_ORDERS, OWNER. */
  invoices: Array<Invoice>;
  /** Informs if an order is fully paid. */
  isPaid: Scalars['Boolean']['output'];
  /** Returns True, if order requires shipping. */
  isShippingRequired: Scalars['Boolean']['output'];
  /** @deprecated This field will be removed in Saleor 4.0. Use the `languageCodeEnum` field to fetch the language code.  */
  languageCode: Scalars['String']['output'];
  /** Order language code. */
  languageCodeEnum: LanguageCodeEnum;
  /** List of order lines. */
  lines: Array<OrderLine>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** User-friendly number of an order. */
  number: Scalars['String']['output'];
  /** The order origin. */
  origin: OrderOriginEnum;
  /** The ID of the order that was the base for this order. */
  original?: Maybe<Scalars['ID']['output']>;
  /** Internal payment status. */
  paymentStatus: PaymentChargeStatusEnum;
  /** User-friendly payment status. */
  paymentStatusDisplay: Scalars['String']['output'];
  /** List of payments for the order. */
  payments: Array<Payment>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  redirectUrl?: Maybe<Scalars['String']['output']>;
  /** Shipping address. The full data can be access for orders created in Saleor 3.2 and later, for other orders requires one of the following permissions: MANAGE_ORDERS, OWNER. */
  shippingAddress?: Maybe<Address>;
  /**
   * Shipping method for this order.
   * @deprecated This field will be removed in Saleor 4.0. Use `deliveryMethod` instead.
   */
  shippingMethod?: Maybe<ShippingMethod>;
  shippingMethodName?: Maybe<Scalars['String']['output']>;
  /** Shipping methods related to this order. */
  shippingMethods: Array<ShippingMethod>;
  /** Total price of shipping. */
  shippingPrice: TaxedMoney;
  /**
   * Denormalized tax class assigned to the shipping method.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  shippingTaxClass?: Maybe<TaxClass>;
  /**
   * Denormalized public metadata of the shipping method's tax class.
   *
   * Added in Saleor 3.9.
   */
  shippingTaxClassMetadata: Array<MetadataItem>;
  /**
   * Denormalized name of the tax class assigned to the shipping method.
   *
   * Added in Saleor 3.9.
   */
  shippingTaxClassName?: Maybe<Scalars['String']['output']>;
  /**
   * Denormalized private metadata of the shipping method's tax class. Requires staff permissions to access.
   *
   * Added in Saleor 3.9.
   */
  shippingTaxClassPrivateMetadata: Array<MetadataItem>;
  /** The shipping tax rate value. */
  shippingTaxRate: Scalars['Float']['output'];
  status: OrderStatus;
  /** User-friendly order status. */
  statusDisplay: Scalars['String']['output'];
  /** The sum of line prices not including shipping. */
  subtotal: TaxedMoney;
  /**
   * Returns True if order has to be exempt from taxes.
   *
   * Added in Saleor 3.8.
   */
  taxExemption: Scalars['Boolean']['output'];
  /** @deprecated This field will be removed in Saleor 4.0. Use `id` instead. */
  token: Scalars['String']['output'];
  /** Total amount of the order. */
  total: TaxedMoney;
  /**
   * Total amount of ongoing authorize requests for the order's transactions.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalAuthorizePending: Money;
  /** Amount authorized for the order. */
  totalAuthorized: Money;
  /** The difference between the paid and the order total amount. */
  totalBalance: Money;
  /**
   * Total amount of ongoing cancel requests for the order's transactions.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalCancelPending: Money;
  /**
   * Amount canceled for the order.
   *
   * Added in Saleor 3.13.
   */
  totalCanceled: Money;
  /**
   * Amount captured for the order.
   * @deprecated This field will be removed in Saleor 4.0. Use `totalCharged` instead.
   */
  totalCaptured: Money;
  /**
   * Total amount of ongoing charge requests for the order's transactions.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalChargePending: Money;
  /**
   * Amount charged for the order.
   *
   * Added in Saleor 3.13.
   */
  totalCharged: Money;
  /**
   * Total amount of granted refund.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalGrantedRefund: Money;
  /**
   * Total amount of ongoing refund requests for the order's transactions.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalRefundPending: Money;
  /**
   * Total refund amount for the order.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  totalRefunded: Money;
  /**
   * The difference amount between granted refund and the amounts that are pending and refunded.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  totalRemainingGrant: Money;
  trackingClientId: Scalars['String']['output'];
  /**
   * List of transactions for the order. Requires one of the following permissions: MANAGE_ORDERS, HANDLE_PAYMENTS.
   *
   * Added in Saleor 3.4.
   */
  transactions: Array<TransactionItem>;
  /**
   * Translated discount name.
   * @deprecated This field will be removed in Saleor 4.0. Use the `discounts` field instead.
   */
  translatedDiscountName?: Maybe<Scalars['String']['output']>;
  /** Undiscounted total amount of the order. */
  undiscountedTotal: TaxedMoney;
  updatedAt: Scalars['DateTime']['output'];
  /** User who placed the order. This field is set only for orders placed by authenticated users. Can be fetched for orders created in Saleor 3.2 and later, for other orders requires one of the following permissions: MANAGE_USERS, MANAGE_ORDERS, OWNER. */
  user?: Maybe<User>;
  /** Email address of the customer. The full data can be access for orders created in Saleor 3.2 and later, for other orders requires one of the following permissions: MANAGE_ORDERS, OWNER. */
  userEmail?: Maybe<Scalars['String']['output']>;
  voucher?: Maybe<Voucher>;
  weight: Weight;
};


/** Represents an order in the shop. */
export type OrderMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an order in the shop. */
export type OrderMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents an order in the shop. */
export type OrderPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an order in the shop. */
export type OrderPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export enum OrderAction {
  /** Represents the capture action. */
  Capture = 'CAPTURE',
  /** Represents a mark-as-paid action. */
  MarkAsPaid = 'MARK_AS_PAID',
  /** Represents a refund action. */
  Refund = 'REFUND',
  /** Represents a void action. */
  Void = 'VOID'
}

/**
 * Adds note to the order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderAddNote = {
  __typename?: 'OrderAddNote';
  errors: Array<OrderError>;
  /** Order note created. */
  event?: Maybe<OrderEvent>;
  /** Order with the note added. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderAddNoteInput = {
  /** Note message. */
  message: Scalars['String']['input'];
};

/**
 * Determine a current authorize status for order.
 *
 *     We treat the order as fully authorized when the sum of authorized and charged funds
 *     cover the `order.total`-`order.totalGrantedRefund`.
 *     We treat the order as partially authorized when the sum of authorized and charged
 *     funds covers only part of the `order.total`-`order.totalGrantedRefund`.
 *     We treat the order as not authorized when the sum of authorized and charged funds is
 *     0.
 *
 *     NONE - the funds are not authorized
 *     PARTIAL - the funds that are authorized and charged don't cover fully the
 *     `order.total`-`order.totalGrantedRefund`
 *     FULL - the funds that are authorized and charged fully cover the
 *     `order.total`-`order.totalGrantedRefund`
 *
 */
export enum OrderAuthorizeStatusEnum {
  Full = 'FULL',
  None = 'NONE',
  Partial = 'PARTIAL'
}

/**
 * Cancels orders.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderBulkCancel = {
  __typename?: 'OrderBulkCancel';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<OrderError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Cancel an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderCancel = {
  __typename?: 'OrderCancel';
  errors: Array<OrderError>;
  /** Canceled order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when order is canceled.
 *
 * Added in Saleor 3.2.
 */
export type OrderCancelled = Event & {
  __typename?: 'OrderCancelled';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Capture an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderCapture = {
  __typename?: 'OrderCapture';
  errors: Array<OrderError>;
  /** Captured order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Determine the current charge status for the order.
 *
 *     An order is considered overcharged when the sum of the
 *     transactionItem's charge amounts exceeds the value of
 *     `order.total` - `order.totalGrantedRefund`.
 *     If the sum of the transactionItem's charge amounts equals
 *     `order.total` - `order.totalGrantedRefund`, we consider the order to be fully
 *     charged.
 *     If the sum of the transactionItem's charge amounts covers a part of the
 *     `order.total` - `order.totalGrantedRefund`, we treat the order as partially charged.
 *
 *     NONE - the funds are not charged.
 *     PARTIAL - the funds that are charged don't cover the
 *     `order.total`-`order.totalGrantedRefund`
 *     FULL - the funds that are charged fully cover the
 *     `order.total`-`order.totalGrantedRefund`
 *     OVERCHARGED - the charged funds are bigger than the
 *     `order.total`-`order.totalGrantedRefund`
 *
 */
export enum OrderChargeStatusEnum {
  Full = 'FULL',
  None = 'NONE',
  Overcharged = 'OVERCHARGED',
  Partial = 'PARTIAL'
}

/**
 * Confirms an unconfirmed order by changing status to unfulfilled.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderConfirm = {
  __typename?: 'OrderConfirm';
  errors: Array<OrderError>;
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when order is confirmed.
 *
 * Added in Saleor 3.2.
 */
export type OrderConfirmed = Event & {
  __typename?: 'OrderConfirmed';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type OrderCountableConnection = {
  __typename?: 'OrderCountableConnection';
  edges: Array<OrderCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type OrderCountableEdge = {
  __typename?: 'OrderCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Order;
};

/**
 * Create new order from existing checkout. Requires the following permissions: AUTHENTICATED_APP and HANDLE_CHECKOUTS.
 *
 * Added in Saleor 3.2.
 */
export type OrderCreateFromCheckout = {
  __typename?: 'OrderCreateFromCheckout';
  errors: Array<OrderCreateFromCheckoutError>;
  /** Placed order. */
  order?: Maybe<Order>;
};

export type OrderCreateFromCheckoutError = {
  __typename?: 'OrderCreateFromCheckoutError';
  /** The error code. */
  code: OrderCreateFromCheckoutErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** List of line Ids which cause the error. */
  lines?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of variant IDs which causes the error. */
  variants?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum OrderCreateFromCheckoutErrorCode {
  BillingAddressNotSet = 'BILLING_ADDRESS_NOT_SET',
  ChannelInactive = 'CHANNEL_INACTIVE',
  CheckoutNotFound = 'CHECKOUT_NOT_FOUND',
  EmailNotSet = 'EMAIL_NOT_SET',
  GiftCardNotApplicable = 'GIFT_CARD_NOT_APPLICABLE',
  GraphqlError = 'GRAPHQL_ERROR',
  InsufficientStock = 'INSUFFICIENT_STOCK',
  InvalidShippingMethod = 'INVALID_SHIPPING_METHOD',
  NoLines = 'NO_LINES',
  ShippingAddressNotSet = 'SHIPPING_ADDRESS_NOT_SET',
  ShippingMethodNotSet = 'SHIPPING_METHOD_NOT_SET',
  TaxError = 'TAX_ERROR',
  UnavailableVariantInChannel = 'UNAVAILABLE_VARIANT_IN_CHANNEL',
  VoucherNotApplicable = 'VOUCHER_NOT_APPLICABLE'
}

/**
 * Event sent when new order is created.
 *
 * Added in Saleor 3.2.
 */
export type OrderCreated = Event & {
  __typename?: 'OrderCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export enum OrderDirection {
  /** Specifies an ascending sort order. */
  Asc = 'ASC',
  /** Specifies a descending sort order. */
  Desc = 'DESC'
}

/** Contains all details related to the applied discount to the order. */
export type OrderDiscount = Node & {
  __typename?: 'OrderDiscount';
  /** Returns amount of discount. */
  amount: Money;
  id: Scalars['ID']['output'];
  name?: Maybe<Scalars['String']['output']>;
  /**
   * Explanation for the applied discount.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  reason?: Maybe<Scalars['String']['output']>;
  translatedName?: Maybe<Scalars['String']['output']>;
  type: OrderDiscountType;
  /** Value of the discount. Can store fixed value or percent value */
  value: Scalars['PositiveDecimal']['output'];
  /** Type of the discount: fixed or percent */
  valueType: DiscountValueTypeEnum;
};

/**
 * Adds discount to the order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderDiscountAdd = {
  __typename?: 'OrderDiscountAdd';
  errors: Array<OrderError>;
  /** Order which has been discounted. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderDiscountCommonInput = {
  /** Explanation for the applied discount. */
  reason?: InputMaybe<Scalars['String']['input']>;
  /** Value of the discount. Can store fixed value or percent value */
  value: Scalars['PositiveDecimal']['input'];
  /** Type of the discount: fixed or percent */
  valueType: DiscountValueTypeEnum;
};

/**
 * Remove discount from the order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderDiscountDelete = {
  __typename?: 'OrderDiscountDelete';
  errors: Array<OrderError>;
  /** Order which has removed discount. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/** An enumeration. */
export enum OrderDiscountType {
  Manual = 'MANUAL',
  Sale = 'SALE',
  Voucher = 'VOUCHER'
}

/**
 * Update discount for the order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderDiscountUpdate = {
  __typename?: 'OrderDiscountUpdate';
  errors: Array<OrderError>;
  /** Order which has been discounted. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderDraftFilterInput = {
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  created?: InputMaybe<DateRangeInput>;
  customer?: InputMaybe<Scalars['String']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
};

export type OrderError = {
  __typename?: 'OrderError';
  /** A type of address that causes the error. */
  addressType?: Maybe<AddressTypeEnum>;
  /** The error code. */
  code: OrderErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of order line IDs that cause the error. */
  orderLines?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of product variants that are associated with the error */
  variants?: Maybe<Array<Scalars['ID']['output']>>;
  /** Warehouse ID which causes the error. */
  warehouse?: Maybe<Scalars['ID']['output']>;
};

/** An enumeration. */
export enum OrderErrorCode {
  BillingAddressNotSet = 'BILLING_ADDRESS_NOT_SET',
  CannotCancelFulfillment = 'CANNOT_CANCEL_FULFILLMENT',
  CannotCancelOrder = 'CANNOT_CANCEL_ORDER',
  CannotDelete = 'CANNOT_DELETE',
  CannotDiscount = 'CANNOT_DISCOUNT',
  CannotFulfillUnpaidOrder = 'CANNOT_FULFILL_UNPAID_ORDER',
  CannotRefund = 'CANNOT_REFUND',
  CaptureInactivePayment = 'CAPTURE_INACTIVE_PAYMENT',
  ChannelInactive = 'CHANNEL_INACTIVE',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  FulfillOrderLine = 'FULFILL_ORDER_LINE',
  GiftCardLine = 'GIFT_CARD_LINE',
  GraphqlError = 'GRAPHQL_ERROR',
  InsufficientStock = 'INSUFFICIENT_STOCK',
  Invalid = 'INVALID',
  InvalidQuantity = 'INVALID_QUANTITY',
  NotAvailableInChannel = 'NOT_AVAILABLE_IN_CHANNEL',
  NotEditable = 'NOT_EDITABLE',
  NotFound = 'NOT_FOUND',
  OrderNoShippingAddress = 'ORDER_NO_SHIPPING_ADDRESS',
  PaymentError = 'PAYMENT_ERROR',
  PaymentMissing = 'PAYMENT_MISSING',
  ProductNotPublished = 'PRODUCT_NOT_PUBLISHED',
  ProductUnavailableForPurchase = 'PRODUCT_UNAVAILABLE_FOR_PURCHASE',
  Required = 'REQUIRED',
  ShippingMethodNotApplicable = 'SHIPPING_METHOD_NOT_APPLICABLE',
  ShippingMethodRequired = 'SHIPPING_METHOD_REQUIRED',
  TaxError = 'TAX_ERROR',
  TransactionError = 'TRANSACTION_ERROR',
  Unique = 'UNIQUE',
  VoidInactivePayment = 'VOID_INACTIVE_PAYMENT',
  ZeroQuantity = 'ZERO_QUANTITY'
}

/** History log of the order. */
export type OrderEvent = Node & {
  __typename?: 'OrderEvent';
  /** Amount of money. */
  amount?: Maybe<Scalars['Float']['output']>;
  /** App that performed the action. Requires of of the following permissions: MANAGE_APPS, MANAGE_ORDERS, OWNER. */
  app?: Maybe<App>;
  /** Composed ID of the Fulfillment. */
  composedId?: Maybe<Scalars['String']['output']>;
  /** Date when event happened at in ISO 8601 format. */
  date?: Maybe<Scalars['DateTime']['output']>;
  /** The discount applied to the order. */
  discount?: Maybe<OrderEventDiscountObject>;
  /** Email of the customer. */
  email?: Maybe<Scalars['String']['output']>;
  /** Type of an email sent to the customer. */
  emailType?: Maybe<OrderEventsEmailsEnum>;
  /** The lines fulfilled. */
  fulfilledItems?: Maybe<Array<FulfillmentLine>>;
  id: Scalars['ID']['output'];
  /** Number of an invoice related to the order. */
  invoiceNumber?: Maybe<Scalars['String']['output']>;
  /** The concerned lines. */
  lines?: Maybe<Array<OrderEventOrderLineObject>>;
  /** Content of the event. */
  message?: Maybe<Scalars['String']['output']>;
  /** User-friendly number of an order. */
  orderNumber?: Maybe<Scalars['String']['output']>;
  /** List of oversold lines names. */
  oversoldItems?: Maybe<Array<Scalars['String']['output']>>;
  /** The payment gateway of the payment. */
  paymentGateway?: Maybe<Scalars['String']['output']>;
  /** The payment reference from the payment provider. */
  paymentId?: Maybe<Scalars['String']['output']>;
  /** Number of items. */
  quantity?: Maybe<Scalars['Int']['output']>;
  /** The reference of payment's transaction. */
  reference?: Maybe<Scalars['String']['output']>;
  /** The order which is related to this order. */
  relatedOrder?: Maybe<Order>;
  /** Define if shipping costs were included to the refund. */
  shippingCostsIncluded?: Maybe<Scalars['Boolean']['output']>;
  /**
   * The status of payment's transaction.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature).Use `TransactionEvent` to track the status of `TransactionItem`.
   */
  status?: Maybe<TransactionStatus>;
  /** The transaction reference of captured payment. */
  transactionReference?: Maybe<Scalars['String']['output']>;
  /** Order event type. */
  type?: Maybe<OrderEventsEnum>;
  /** User who performed the action. */
  user?: Maybe<User>;
  /** The warehouse were items were restocked. */
  warehouse?: Maybe<Warehouse>;
};

export type OrderEventCountableConnection = {
  __typename?: 'OrderEventCountableConnection';
  edges: Array<OrderEventCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type OrderEventCountableEdge = {
  __typename?: 'OrderEventCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: OrderEvent;
};

export type OrderEventDiscountObject = {
  __typename?: 'OrderEventDiscountObject';
  /** Returns amount of discount. */
  amount?: Maybe<Money>;
  /** Returns amount of discount. */
  oldAmount?: Maybe<Money>;
  /** Value of the discount. Can store fixed value or percent value. */
  oldValue?: Maybe<Scalars['PositiveDecimal']['output']>;
  /** Type of the discount: fixed or percent. */
  oldValueType?: Maybe<DiscountValueTypeEnum>;
  /** Explanation for the applied discount. */
  reason?: Maybe<Scalars['String']['output']>;
  /** Value of the discount. Can store fixed value or percent value. */
  value: Scalars['PositiveDecimal']['output'];
  /** Type of the discount: fixed or percent. */
  valueType: DiscountValueTypeEnum;
};

export type OrderEventOrderLineObject = {
  __typename?: 'OrderEventOrderLineObject';
  /** The discount applied to the order line. */
  discount?: Maybe<OrderEventDiscountObject>;
  /** The variant name. */
  itemName?: Maybe<Scalars['String']['output']>;
  /** The order line. */
  orderLine?: Maybe<OrderLine>;
  /** The variant quantity. */
  quantity?: Maybe<Scalars['Int']['output']>;
};

/** An enumeration. */
export enum OrderEventsEmailsEnum {
  Confirmed = 'CONFIRMED',
  DigitalLinks = 'DIGITAL_LINKS',
  FulfillmentConfirmation = 'FULFILLMENT_CONFIRMATION',
  OrderCancel = 'ORDER_CANCEL',
  OrderConfirmation = 'ORDER_CONFIRMATION',
  OrderRefund = 'ORDER_REFUND',
  PaymentConfirmation = 'PAYMENT_CONFIRMATION',
  ShippingConfirmation = 'SHIPPING_CONFIRMATION',
  TrackingUpdated = 'TRACKING_UPDATED'
}

/** The different order event types.  */
export enum OrderEventsEnum {
  AddedProducts = 'ADDED_PRODUCTS',
  Canceled = 'CANCELED',
  Confirmed = 'CONFIRMED',
  DraftCreated = 'DRAFT_CREATED',
  DraftCreatedFromReplace = 'DRAFT_CREATED_FROM_REPLACE',
  EmailSent = 'EMAIL_SENT',
  Expired = 'EXPIRED',
  ExternalServiceNotification = 'EXTERNAL_SERVICE_NOTIFICATION',
  FulfillmentAwaitsApproval = 'FULFILLMENT_AWAITS_APPROVAL',
  FulfillmentCanceled = 'FULFILLMENT_CANCELED',
  FulfillmentFulfilledItems = 'FULFILLMENT_FULFILLED_ITEMS',
  FulfillmentRefunded = 'FULFILLMENT_REFUNDED',
  FulfillmentReplaced = 'FULFILLMENT_REPLACED',
  FulfillmentRestockedItems = 'FULFILLMENT_RESTOCKED_ITEMS',
  FulfillmentReturned = 'FULFILLMENT_RETURNED',
  InvoiceGenerated = 'INVOICE_GENERATED',
  InvoiceRequested = 'INVOICE_REQUESTED',
  InvoiceSent = 'INVOICE_SENT',
  InvoiceUpdated = 'INVOICE_UPDATED',
  NoteAdded = 'NOTE_ADDED',
  OrderDiscountAdded = 'ORDER_DISCOUNT_ADDED',
  OrderDiscountAutomaticallyUpdated = 'ORDER_DISCOUNT_AUTOMATICALLY_UPDATED',
  OrderDiscountDeleted = 'ORDER_DISCOUNT_DELETED',
  OrderDiscountUpdated = 'ORDER_DISCOUNT_UPDATED',
  OrderFullyPaid = 'ORDER_FULLY_PAID',
  OrderLineDiscountRemoved = 'ORDER_LINE_DISCOUNT_REMOVED',
  OrderLineDiscountUpdated = 'ORDER_LINE_DISCOUNT_UPDATED',
  OrderLineProductDeleted = 'ORDER_LINE_PRODUCT_DELETED',
  OrderLineVariantDeleted = 'ORDER_LINE_VARIANT_DELETED',
  OrderMarkedAsPaid = 'ORDER_MARKED_AS_PAID',
  OrderReplacementCreated = 'ORDER_REPLACEMENT_CREATED',
  Other = 'OTHER',
  OversoldItems = 'OVERSOLD_ITEMS',
  PaymentAuthorized = 'PAYMENT_AUTHORIZED',
  PaymentCaptured = 'PAYMENT_CAPTURED',
  PaymentFailed = 'PAYMENT_FAILED',
  PaymentRefunded = 'PAYMENT_REFUNDED',
  PaymentVoided = 'PAYMENT_VOIDED',
  Placed = 'PLACED',
  PlacedFromDraft = 'PLACED_FROM_DRAFT',
  RemovedProducts = 'REMOVED_PRODUCTS',
  TrackingUpdated = 'TRACKING_UPDATED',
  TransactionCancelRequested = 'TRANSACTION_CANCEL_REQUESTED',
  /** This field will be removed in Saleor 3.14 (Preview Feature). Use `TRANSACTION_CHARGE_REQUESTED` instead. */
  TransactionCaptureRequested = 'TRANSACTION_CAPTURE_REQUESTED',
  TransactionChargeRequested = 'TRANSACTION_CHARGE_REQUESTED',
  TransactionEvent = 'TRANSACTION_EVENT',
  TransactionMarkAsPaidFailed = 'TRANSACTION_MARK_AS_PAID_FAILED',
  TransactionRefundRequested = 'TRANSACTION_REFUND_REQUESTED',
  /** This field will be removed in Saleor 3.14 (Preview Feature). Use `TRANSACTION_CANCEL_REQUESTED` instead. */
  TransactionVoidRequested = 'TRANSACTION_VOID_REQUESTED',
  UpdatedAddress = 'UPDATED_ADDRESS'
}

/**
 * Event sent when order becomes expired.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type OrderExpired = Event & {
  __typename?: 'OrderExpired';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type OrderFilterInput = {
  authorizeStatus?: InputMaybe<Array<OrderAuthorizeStatusEnum>>;
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  chargeStatus?: InputMaybe<Array<OrderChargeStatusEnum>>;
  checkoutIds?: InputMaybe<Array<Scalars['ID']['input']>>;
  created?: InputMaybe<DateRangeInput>;
  customer?: InputMaybe<Scalars['String']['input']>;
  giftCardBought?: InputMaybe<Scalars['Boolean']['input']>;
  giftCardUsed?: InputMaybe<Scalars['Boolean']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  isClickAndCollect?: InputMaybe<Scalars['Boolean']['input']>;
  isPreorder?: InputMaybe<Scalars['Boolean']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  numbers?: InputMaybe<Array<Scalars['String']['input']>>;
  paymentStatus?: InputMaybe<Array<PaymentChargeStatusEnum>>;
  search?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<Array<OrderStatusFilter>>;
  updatedAt?: InputMaybe<DateTimeRangeInput>;
};

/**
 * Filter shipping methods for order.
 *
 * Added in Saleor 3.6.
 */
export type OrderFilterShippingMethods = Event & {
  __typename?: 'OrderFilterShippingMethods';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /**
   * Shipping methods that can be used with this checkout.
   *
   * Added in Saleor 3.6.
   */
  shippingMethods?: Maybe<Array<ShippingMethod>>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Creates new fulfillments for an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderFulfill = {
  __typename?: 'OrderFulfill';
  errors: Array<OrderError>;
  /** List of created fulfillments. */
  fulfillments?: Maybe<Array<Fulfillment>>;
  /** Fulfilled order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderFulfillInput = {
  /** If true, then allow proceed fulfillment when stock is exceeded. */
  allowStockToBeExceeded?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of items informing how to fulfill the order. */
  lines: Array<OrderFulfillLineInput>;
  /** If true, send an email notification to the customer. */
  notifyCustomer?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Fulfillment tracking number.
   *
   * Added in Saleor 3.6.
   */
  trackingNumber?: InputMaybe<Scalars['String']['input']>;
};

export type OrderFulfillLineInput = {
  /** The ID of the order line. */
  orderLineId?: InputMaybe<Scalars['ID']['input']>;
  /** List of stock items to create. */
  stocks: Array<OrderFulfillStockInput>;
};

export type OrderFulfillStockInput = {
  /** The number of line items to be fulfilled from given warehouse. */
  quantity: Scalars['Int']['input'];
  /** ID of the warehouse from which the item will be fulfilled. */
  warehouse: Scalars['ID']['input'];
};

/**
 * Event sent when order is fulfilled.
 *
 * Added in Saleor 3.2.
 */
export type OrderFulfilled = Event & {
  __typename?: 'OrderFulfilled';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when order is fully paid.
 *
 * Added in Saleor 3.2.
 */
export type OrderFullyPaid = Event & {
  __typename?: 'OrderFullyPaid';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * The order is fully refunded.
 *
 * Added in Saleor 3.14.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type OrderFullyRefunded = Event & {
  __typename?: 'OrderFullyRefunded';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Adds granted refund to the order.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderGrantRefundCreate = {
  __typename?: 'OrderGrantRefundCreate';
  errors: Array<OrderGrantRefundCreateError>;
  /** Created granted refund. */
  grantedRefund?: Maybe<OrderGrantedRefund>;
  /** Order which has assigned new grant refund. */
  order?: Maybe<Order>;
};

export type OrderGrantRefundCreateError = {
  __typename?: 'OrderGrantRefundCreateError';
  /** The error code. */
  code: OrderGrantRefundCreateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum OrderGrantRefundCreateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  NotFound = 'NOT_FOUND'
}

export type OrderGrantRefundCreateInput = {
  /** Amount of the granted refund. */
  amount: Scalars['Decimal']['input'];
  /** Reason of the granted refund. */
  reason?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Updates granted refund.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderGrantRefundUpdate = {
  __typename?: 'OrderGrantRefundUpdate';
  errors: Array<OrderGrantRefundUpdateError>;
  /** Created granted refund. */
  grantedRefund?: Maybe<OrderGrantedRefund>;
  /** Order which has assigned updated grant refund. */
  order?: Maybe<Order>;
  orderGrantedRefund?: Maybe<OrderGrantedRefund>;
};

export type OrderGrantRefundUpdateError = {
  __typename?: 'OrderGrantRefundUpdateError';
  /** The error code. */
  code: OrderGrantRefundUpdateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum OrderGrantRefundUpdateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED'
}

export type OrderGrantRefundUpdateInput = {
  /** Amount of the granted refund. */
  amount?: InputMaybe<Scalars['Decimal']['input']>;
  /** Reason of the granted refund. */
  reason?: InputMaybe<Scalars['String']['input']>;
};

/**
 * The details of granted refund.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type OrderGrantedRefund = {
  __typename?: 'OrderGrantedRefund';
  /** Refund amount. */
  amount: Money;
  /** App that performed the action. */
  app?: Maybe<App>;
  /** Time of creation. */
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Reason of the refund. */
  reason?: Maybe<Scalars['String']['output']>;
  /** Time of last update. */
  updatedAt: Scalars['DateTime']['output'];
  /** User who performed the action. Requires of of the following permissions: MANAGE_USERS, MANAGE_STAFF, OWNER. */
  user?: Maybe<User>;
};

/** Represents order line of particular order. */
export type OrderLine = Node & ObjectWithMetadata & {
  __typename?: 'OrderLine';
  /**
   * List of allocations across warehouses.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  allocations?: Maybe<Array<Allocation>>;
  digitalContentUrl?: Maybe<DigitalContentUrl>;
  id: Scalars['ID']['output'];
  isShippingRequired: Scalars['Boolean']['output'];
  /**
   * List of public metadata items. Can be accessed without permissions.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * List of private metadata items. Requires staff permissions to access.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.5.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  productName: Scalars['String']['output'];
  productSku?: Maybe<Scalars['String']['output']>;
  productVariantId?: Maybe<Scalars['String']['output']>;
  quantity: Scalars['Int']['output'];
  quantityFulfilled: Scalars['Int']['output'];
  /**
   * A quantity of items remaining to be fulfilled.
   *
   * Added in Saleor 3.1.
   */
  quantityToFulfill: Scalars['Int']['output'];
  /**
   * Denormalized tax class of the product in this order line.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClass?: Maybe<TaxClass>;
  /**
   * Denormalized public metadata of the tax class.
   *
   * Added in Saleor 3.9.
   */
  taxClassMetadata: Array<MetadataItem>;
  /**
   * Denormalized name of the tax class.
   *
   * Added in Saleor 3.9.
   */
  taxClassName?: Maybe<Scalars['String']['output']>;
  /**
   * Denormalized private metadata of the tax class. Requires staff permissions to access.
   *
   * Added in Saleor 3.9.
   */
  taxClassPrivateMetadata: Array<MetadataItem>;
  taxRate: Scalars['Float']['output'];
  thumbnail?: Maybe<Image>;
  /** Price of the order line. */
  totalPrice: TaxedMoney;
  /** Product name in the customer's language */
  translatedProductName: Scalars['String']['output'];
  /** Variant name in the customer's language */
  translatedVariantName: Scalars['String']['output'];
  /** Price of the single item in the order line without applied an order line discount. */
  undiscountedUnitPrice: TaxedMoney;
  /** The discount applied to the single order line. */
  unitDiscount: Money;
  unitDiscountReason?: Maybe<Scalars['String']['output']>;
  /** Type of the discount: fixed or percent */
  unitDiscountType?: Maybe<DiscountValueTypeEnum>;
  /** Value of the discount. Can store fixed value or percent value */
  unitDiscountValue: Scalars['PositiveDecimal']['output'];
  /** Price of the single item in the order line. */
  unitPrice: TaxedMoney;
  /** A purchased product variant. Note: this field may be null if the variant has been removed from stock at all. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  variant?: Maybe<ProductVariant>;
  variantName: Scalars['String']['output'];
};


/** Represents order line of particular order. */
export type OrderLineMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents order line of particular order. */
export type OrderLineMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents order line of particular order. */
export type OrderLinePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents order line of particular order. */
export type OrderLinePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents order line of particular order. */
export type OrderLineThumbnailArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};

export type OrderLineCreateInput = {
  /**
   * Flag that allow force splitting the same variant into multiple lines by skipping the matching logic.
   *
   * Added in Saleor 3.6.
   */
  forceNewLine?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Custom price of the item.When the line with the same variant will be provided multiple times, the last price will be used.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  price?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** Number of variant items ordered. */
  quantity: Scalars['Int']['input'];
  /** Product variant ID. */
  variantId: Scalars['ID']['input'];
};

/**
 * Deletes an order line from an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderLineDelete = {
  __typename?: 'OrderLineDelete';
  errors: Array<OrderError>;
  /** A related order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  /** An order line that was deleted. */
  orderLine?: Maybe<OrderLine>;
};

/**
 * Remove discount applied to the order line.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderLineDiscountRemove = {
  __typename?: 'OrderLineDiscountRemove';
  errors: Array<OrderError>;
  /** Order which is related to line which has removed discount. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  /** Order line which has removed discount. */
  orderLine?: Maybe<OrderLine>;
};

/**
 * Update discount for the order line.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderLineDiscountUpdate = {
  __typename?: 'OrderLineDiscountUpdate';
  errors: Array<OrderError>;
  /** Order which is related to the discounted line. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  /** Order line which has been discounted. */
  orderLine?: Maybe<OrderLine>;
};

export type OrderLineInput = {
  /** Number of variant items ordered. */
  quantity: Scalars['Int']['input'];
};

/**
 * Updates an order line of an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderLineUpdate = {
  __typename?: 'OrderLineUpdate';
  errors: Array<OrderError>;
  /** Related order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  orderLine?: Maybe<OrderLine>;
};

/**
 * Create order lines for an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderLinesCreate = {
  __typename?: 'OrderLinesCreate';
  errors: Array<OrderError>;
  /** Related order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
  /** List of added order lines. */
  orderLines?: Maybe<Array<OrderLine>>;
};

/**
 * Mark order as manually paid.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderMarkAsPaid = {
  __typename?: 'OrderMarkAsPaid';
  errors: Array<OrderError>;
  /** Order marked as paid. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/**
 * Event sent when order metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type OrderMetadataUpdated = Event & {
  __typename?: 'OrderMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type OrderOrCheckout = Checkout | Order;

/** An enumeration. */
export enum OrderOriginEnum {
  Checkout = 'CHECKOUT',
  Draft = 'DRAFT',
  Reissue = 'REISSUE'
}

/**
 * Payment has been made. The order may be partially or fully paid.
 *
 * Added in Saleor 3.14.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type OrderPaid = Event & {
  __typename?: 'OrderPaid';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Refund an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderRefund = {
  __typename?: 'OrderRefund';
  errors: Array<OrderError>;
  /** A refunded order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderRefundFulfillmentLineInput = {
  /** The ID of the fulfillment line to refund. */
  fulfillmentLineId: Scalars['ID']['input'];
  /** The number of items to be refunded. */
  quantity: Scalars['Int']['input'];
};

export type OrderRefundLineInput = {
  /** The ID of the order line to refund. */
  orderLineId: Scalars['ID']['input'];
  /** The number of items to be refunded. */
  quantity: Scalars['Int']['input'];
};

export type OrderRefundProductsInput = {
  /** The total amount of refund when the value is provided manually. */
  amountToRefund?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** List of fulfilled lines to refund. */
  fulfillmentLines?: InputMaybe<Array<OrderRefundFulfillmentLineInput>>;
  /** If true, Saleor will refund shipping costs. If amountToRefund is providedincludeShippingCosts will be ignored. */
  includeShippingCosts?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of unfulfilled lines to refund. */
  orderLines?: InputMaybe<Array<OrderRefundLineInput>>;
};

/**
 * The order received a refund. The order may be partially or fully refunded.
 *
 * Added in Saleor 3.14.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type OrderRefunded = Event & {
  __typename?: 'OrderRefunded';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type OrderReturnFulfillmentLineInput = {
  /** The ID of the fulfillment line to return. */
  fulfillmentLineId: Scalars['ID']['input'];
  /** The number of items to be returned. */
  quantity: Scalars['Int']['input'];
  /** Determines, if the line should be added to replace order. */
  replace?: InputMaybe<Scalars['Boolean']['input']>;
};

export type OrderReturnLineInput = {
  /** The ID of the order line to return. */
  orderLineId: Scalars['ID']['input'];
  /** The number of items to be returned. */
  quantity: Scalars['Int']['input'];
  /** Determines, if the line should be added to replace order. */
  replace?: InputMaybe<Scalars['Boolean']['input']>;
};

export type OrderReturnProductsInput = {
  /** The total amount of refund when the value is provided manually. */
  amountToRefund?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** List of fulfilled lines to return. */
  fulfillmentLines?: InputMaybe<Array<OrderReturnFulfillmentLineInput>>;
  /** If true, Saleor will refund shipping costs. If amountToRefund is providedincludeShippingCosts will be ignored. */
  includeShippingCosts?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of unfulfilled lines to return. */
  orderLines?: InputMaybe<Array<OrderReturnLineInput>>;
  /** If true, Saleor will call refund action for all lines. */
  refund?: InputMaybe<Scalars['Boolean']['input']>;
};

/** Represents the channel-specific order settings. */
export type OrderSettings = {
  __typename?: 'OrderSettings';
  /** When disabled, all new orders from checkout will be marked as unconfirmed. When enabled orders from checkout will become unfulfilled immediately. */
  automaticallyConfirmAllNewOrders: Scalars['Boolean']['output'];
  /** When enabled, all non-shippable gift card orders will be fulfilled automatically. */
  automaticallyFulfillNonShippableGiftCard: Scalars['Boolean']['output'];
  /**
   * Determine the transaction flow strategy to be used. Include the selected option in the payload sent to the payment app, as a requested action for the transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  defaultTransactionFlowStrategy: TransactionFlowStrategyEnum;
  /**
   * The time in days after expired orders will be deleted.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  deleteExpiredOrdersAfter: Scalars['Day']['output'];
  /**
   * Expiration time in minutes. Default null - means do not expire any orders.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  expireOrdersAfter?: Maybe<Scalars['Minute']['output']>;
  /**
   * Determine what strategy will be used to mark the order as paid. Based on the chosen option, the proper object will be created and attached to the order when it's manually marked as paid.
   * `PAYMENT_FLOW` - [default option] creates the `Payment` object.
   * `TRANSACTION_FLOW` - creates the `TransactionItem` object.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  markAsPaidStrategy: MarkAsPaidStrategyEnum;
};

export type OrderSettingsError = {
  __typename?: 'OrderSettingsError';
  /** The error code. */
  code: OrderSettingsErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum OrderSettingsErrorCode {
  Invalid = 'INVALID'
}

export type OrderSettingsInput = {
  /** When disabled, all new orders from checkout will be marked as unconfirmed. When enabled orders from checkout will become unfulfilled immediately. By default set to True */
  automaticallyConfirmAllNewOrders?: InputMaybe<Scalars['Boolean']['input']>;
  /** When enabled, all non-shippable gift card orders will be fulfilled automatically. By defualt set to True. */
  automaticallyFulfillNonShippableGiftCard?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Determine the transaction flow strategy to be used. Include the selected option in the payload sent to the payment app, as a requested action for the transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  defaultTransactionFlowStrategy?: InputMaybe<TransactionFlowStrategyEnum>;
  /**
   * The time in days after expired orders will be deleted.Allowed range is from 1 to 120.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  deleteExpiredOrdersAfter?: InputMaybe<Scalars['Day']['input']>;
  /**
   * Expiration time in minutes. Default null - means do not expire any orders. Enter 0 or null to disable.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  expireOrdersAfter?: InputMaybe<Scalars['Minute']['input']>;
  /**
   * Determine what strategy will be used to mark the order as paid. Based on the chosen option, the proper object will be created and attached to the order when it's manually marked as paid.
   * `PAYMENT_FLOW` - [default option] creates the `Payment` object.
   * `TRANSACTION_FLOW` - creates the `TransactionItem` object.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  markAsPaidStrategy?: InputMaybe<MarkAsPaidStrategyEnum>;
};

/**
 * Update shop order settings across all channels. Returns `orderSettings` for the first `channel` in alphabetical order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderSettingsUpdate = {
  __typename?: 'OrderSettingsUpdate';
  errors: Array<OrderSettingsError>;
  /** Order settings. */
  orderSettings?: Maybe<OrderSettings>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderSettingsErrors: Array<OrderSettingsError>;
};

export type OrderSettingsUpdateInput = {
  /** When disabled, all new orders from checkout will be marked as unconfirmed. When enabled orders from checkout will become unfulfilled immediately. By default set to True */
  automaticallyConfirmAllNewOrders?: InputMaybe<Scalars['Boolean']['input']>;
  /** When enabled, all non-shippable gift card orders will be fulfilled automatically. By defualt set to True. */
  automaticallyFulfillNonShippableGiftCard?: InputMaybe<Scalars['Boolean']['input']>;
};

export enum OrderSortField {
  /**
   * Sort orders by creation date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  CreatedAt = 'CREATED_AT',
  /**
   * Sort orders by creation date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  CreationDate = 'CREATION_DATE',
  /** Sort orders by customer. */
  Customer = 'CUSTOMER',
  /** Sort orders by fulfillment status. */
  FulfillmentStatus = 'FULFILLMENT_STATUS',
  /** Sort orders by last modified at. */
  LastModifiedAt = 'LAST_MODIFIED_AT',
  /** Sort orders by number. */
  Number = 'NUMBER',
  /** Sort orders by payment. */
  Payment = 'PAYMENT',
  /** Sort orders by rank. Note: This option is available only with the `search` filter. */
  Rank = 'RANK'
}

export type OrderSortingInput = {
  /** Specifies the direction in which to sort orders. */
  direction: OrderDirection;
  /** Sort orders by the selected field. */
  field: OrderSortField;
};

/** An enumeration. */
export enum OrderStatus {
  Canceled = 'CANCELED',
  Draft = 'DRAFT',
  Expired = 'EXPIRED',
  Fulfilled = 'FULFILLED',
  PartiallyFulfilled = 'PARTIALLY_FULFILLED',
  PartiallyReturned = 'PARTIALLY_RETURNED',
  Returned = 'RETURNED',
  Unconfirmed = 'UNCONFIRMED',
  Unfulfilled = 'UNFULFILLED'
}

export enum OrderStatusFilter {
  Canceled = 'CANCELED',
  Fulfilled = 'FULFILLED',
  PartiallyFulfilled = 'PARTIALLY_FULFILLED',
  ReadyToCapture = 'READY_TO_CAPTURE',
  ReadyToFulfill = 'READY_TO_FULFILL',
  Unconfirmed = 'UNCONFIRMED',
  Unfulfilled = 'UNFULFILLED'
}

/**
 * Updates an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderUpdate = {
  __typename?: 'OrderUpdate';
  errors: Array<OrderError>;
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderUpdateInput = {
  /** Billing address of the customer. */
  billingAddress?: InputMaybe<AddressInput>;
  /**
   * External ID of this order.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Shipping address of the customer. */
  shippingAddress?: InputMaybe<AddressInput>;
  /** Email address of the customer. */
  userEmail?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Updates a shipping method of the order. Requires shipping method ID to update, when null is passed then currently assigned shipping method is removed.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderUpdateShipping = {
  __typename?: 'OrderUpdateShipping';
  errors: Array<OrderError>;
  /** Order with updated shipping method. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

export type OrderUpdateShippingInput = {
  /** ID of the selected shipping method, pass null to remove currently assigned shipping method. */
  shippingMethod?: InputMaybe<Scalars['ID']['input']>;
};

/**
 * Event sent when order is updated.
 *
 * Added in Saleor 3.2.
 */
export type OrderUpdated = Event & {
  __typename?: 'OrderUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The order the event relates to. */
  order?: Maybe<Order>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Void an order.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type OrderVoid = {
  __typename?: 'OrderVoid';
  errors: Array<OrderError>;
  /** A voided order. */
  order?: Maybe<Order>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  orderErrors: Array<OrderError>;
};

/** A static page that can be manually added by a shop operator through the dashboard. */
export type Page = Node & ObjectWithMetadata & {
  __typename?: 'Page';
  /** List of attributes assigned to this product. */
  attributes: Array<SelectedAttribute>;
  /**
   * Content of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Content of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `content` field instead.
   */
  contentJson: Scalars['JSONString']['output'];
  created: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  isPublished: Scalars['Boolean']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  pageType: PageType;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** @deprecated This field will be removed in Saleor 4.0. Use the `publishedAt` field to fetch the publication date. */
  publicationDate?: Maybe<Scalars['Date']['output']>;
  /**
   * The page publication date.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  slug: Scalars['String']['output'];
  title: Scalars['String']['output'];
  /** Returns translated page fields for the given language code. */
  translation?: Maybe<PageTranslation>;
};


/** A static page that can be manually added by a shop operator through the dashboard. */
export type PageMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** A static page that can be manually added by a shop operator through the dashboard. */
export type PageMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** A static page that can be manually added by a shop operator through the dashboard. */
export type PagePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** A static page that can be manually added by a shop operator through the dashboard. */
export type PagePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** A static page that can be manually added by a shop operator through the dashboard. */
export type PageTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Assign attributes to a given page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageAttributeAssign = {
  __typename?: 'PageAttributeAssign';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  /** The updated page type. */
  pageType?: Maybe<PageType>;
};

/**
 * Unassign attributes from a given page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageAttributeUnassign = {
  __typename?: 'PageAttributeUnassign';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  /** The updated page type. */
  pageType?: Maybe<PageType>;
};

/**
 * Deletes pages.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageBulkDelete = {
  __typename?: 'PageBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

/**
 * Publish pages.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageBulkPublish = {
  __typename?: 'PageBulkPublish';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

export type PageCountableConnection = {
  __typename?: 'PageCountableConnection';
  edges: Array<PageCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type PageCountableEdge = {
  __typename?: 'PageCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Page;
};

/**
 * Creates a new page.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageCreate = {
  __typename?: 'PageCreate';
  errors: Array<PageError>;
  page?: Maybe<Page>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

export type PageCreateInput = {
  /** List of attributes. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /**
   * Page content.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: InputMaybe<Scalars['JSONString']['input']>;
  /** Determines if page is visible in the storefront. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /** ID of the page type that page belongs to. */
  pageType: Scalars['ID']['input'];
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `publishedAt` field instead.
   */
  publicationDate?: InputMaybe<Scalars['String']['input']>;
  /**
   * Publication date time. ISO 8601 standard.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Page internal name. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** Page title. */
  title?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new page is created.
 *
 * Added in Saleor 3.2.
 */
export type PageCreated = Event & {
  __typename?: 'PageCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page the event relates to. */
  page?: Maybe<Page>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a page.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageDelete = {
  __typename?: 'PageDelete';
  errors: Array<PageError>;
  page?: Maybe<Page>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

/**
 * Event sent when page is deleted.
 *
 * Added in Saleor 3.2.
 */
export type PageDeleted = Event & {
  __typename?: 'PageDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page the event relates to. */
  page?: Maybe<Page>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type PageError = {
  __typename?: 'PageError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: PageErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum PageErrorCode {
  AttributeAlreadyAssigned = 'ATTRIBUTE_ALREADY_ASSIGNED',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type PageFilterInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  pageTypes?: InputMaybe<Array<Scalars['ID']['input']>>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

/** The Relay compliant `PageInfo` type, containing data necessary to paginate this connection. */
export type PageInfo = {
  __typename?: 'PageInfo';
  /** When paginating forwards, the cursor to continue. */
  endCursor?: Maybe<Scalars['String']['output']>;
  /** When paginating forwards, are there more items? */
  hasNextPage: Scalars['Boolean']['output'];
  /** When paginating backwards, are there more items? */
  hasPreviousPage: Scalars['Boolean']['output'];
  /** When paginating backwards, the cursor to continue. */
  startCursor?: Maybe<Scalars['String']['output']>;
};

export type PageInput = {
  /** List of attributes. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /**
   * Page content.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: InputMaybe<Scalars['JSONString']['input']>;
  /** Determines if page is visible in the storefront. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `publishedAt` field instead.
   */
  publicationDate?: InputMaybe<Scalars['String']['input']>;
  /**
   * Publication date time. ISO 8601 standard.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Page internal name. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** Page title. */
  title?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Reorder page attribute values.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageReorderAttributeValues = {
  __typename?: 'PageReorderAttributeValues';
  errors: Array<PageError>;
  /** Page from which attribute values are reordered. */
  page?: Maybe<Page>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

export enum PageSortField {
  /**
   * Sort pages by creation date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  CreatedAt = 'CREATED_AT',
  /**
   * Sort pages by creation date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  CreationDate = 'CREATION_DATE',
  /**
   * Sort pages by publication date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  PublicationDate = 'PUBLICATION_DATE',
  /**
   * Sort pages by publication date.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.
   */
  PublishedAt = 'PUBLISHED_AT',
  /** Sort pages by slug. */
  Slug = 'SLUG',
  /** Sort pages by title. */
  Title = 'TITLE',
  /** Sort pages by visibility. */
  Visibility = 'VISIBILITY'
}

export type PageSortingInput = {
  /** Specifies the direction in which to sort pages. */
  direction: OrderDirection;
  /** Sort pages by the selected field. */
  field: PageSortField;
};

export type PageTranslatableContent = Node & {
  __typename?: 'PageTranslatableContent';
  /** List of page content attribute values that can be translated. */
  attributeValues: Array<AttributeValueTranslatableContent>;
  /**
   * Content of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Content of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `content` field instead.
   */
  contentJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /**
   * A static page that can be manually added by a shop operator through the dashboard.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  page?: Maybe<Page>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  title: Scalars['String']['output'];
  /** Returns translated page fields for the given language code. */
  translation?: Maybe<PageTranslation>;
};


export type PageTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a page.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type PageTranslate = {
  __typename?: 'PageTranslate';
  errors: Array<TranslationError>;
  page?: Maybe<PageTranslatableContent>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type PageTranslation = Node & {
  __typename?: 'PageTranslation';
  /**
   * Translated content of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Translated description of the page.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `content` field instead.
   */
  contentJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
};

export type PageTranslationInput = {
  /**
   * Translated page content.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  content?: InputMaybe<Scalars['JSONString']['input']>;
  seoDescription?: InputMaybe<Scalars['String']['input']>;
  seoTitle?: InputMaybe<Scalars['String']['input']>;
  title?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageType = Node & ObjectWithMetadata & {
  __typename?: 'PageType';
  /** Page attributes of that page type. */
  attributes?: Maybe<Array<Attribute>>;
  /**
   * Attributes that can be assigned to the page type.
   *
   * Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  availableAttributes?: Maybe<AttributeCountableConnection>;
  /**
   * Whether page type has pages assigned.
   *
   * Requires one of the following permissions: MANAGE_PAGES, MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
   */
  hasPages?: Maybe<Scalars['Boolean']['output']>;
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  slug: Scalars['String']['output'];
};


/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageTypeAvailableAttributesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AttributeFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  where?: InputMaybe<AttributeWhereInput>;
};


/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageTypeMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageTypeMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageTypePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a type of page. It defines what attributes are available to pages of this type. */
export type PageTypePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Delete page types.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageTypeBulkDelete = {
  __typename?: 'PageTypeBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

export type PageTypeCountableConnection = {
  __typename?: 'PageTypeCountableConnection';
  edges: Array<PageTypeCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type PageTypeCountableEdge = {
  __typename?: 'PageTypeCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: PageType;
};

/**
 * Create a new page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageTypeCreate = {
  __typename?: 'PageTypeCreate';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  pageType?: Maybe<PageType>;
};

export type PageTypeCreateInput = {
  /** List of attribute IDs to be assigned to the page type. */
  addAttributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Name of the page type. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Page type slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new page type is created.
 *
 * Added in Saleor 3.5.
 */
export type PageTypeCreated = Event & {
  __typename?: 'PageTypeCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page type the event relates to. */
  pageType?: Maybe<PageType>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Delete a page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageTypeDelete = {
  __typename?: 'PageTypeDelete';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  pageType?: Maybe<PageType>;
};

/**
 * Event sent when page type is deleted.
 *
 * Added in Saleor 3.5.
 */
export type PageTypeDeleted = Event & {
  __typename?: 'PageTypeDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page type the event relates to. */
  pageType?: Maybe<PageType>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type PageTypeFilterInput = {
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Reorder the attributes of a page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageTypeReorderAttributes = {
  __typename?: 'PageTypeReorderAttributes';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  /** Page type from which attributes are reordered. */
  pageType?: Maybe<PageType>;
};

export enum PageTypeSortField {
  /** Sort page types by name. */
  Name = 'NAME',
  /** Sort page types by slug. */
  Slug = 'SLUG'
}

export type PageTypeSortingInput = {
  /** Specifies the direction in which to sort page types. */
  direction: OrderDirection;
  /** Sort page types by the selected field. */
  field: PageTypeSortField;
};

/**
 * Update page type.
 *
 * Requires one of the following permissions: MANAGE_PAGE_TYPES_AND_ATTRIBUTES.
 */
export type PageTypeUpdate = {
  __typename?: 'PageTypeUpdate';
  errors: Array<PageError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
  pageType?: Maybe<PageType>;
};

export type PageTypeUpdateInput = {
  /** List of attribute IDs to be assigned to the page type. */
  addAttributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Name of the page type. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** List of attribute IDs to be assigned to the page type. */
  removeAttributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Page type slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when page type is updated.
 *
 * Added in Saleor 3.5.
 */
export type PageTypeUpdated = Event & {
  __typename?: 'PageTypeUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page type the event relates to. */
  pageType?: Maybe<PageType>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Updates an existing page.
 *
 * Requires one of the following permissions: MANAGE_PAGES.
 */
export type PageUpdate = {
  __typename?: 'PageUpdate';
  errors: Array<PageError>;
  page?: Maybe<Page>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pageErrors: Array<PageError>;
};

/**
 * Event sent when page is updated.
 *
 * Added in Saleor 3.2.
 */
export type PageUpdated = Event & {
  __typename?: 'PageUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The page the event relates to. */
  page?: Maybe<Page>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Change the password of the logged in user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type PasswordChange = {
  __typename?: 'PasswordChange';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** A user instance with a new password. */
  user?: Maybe<User>;
};

/** Represents a payment of a given type. */
export type Payment = Node & ObjectWithMetadata & {
  __typename?: 'Payment';
  /**
   * List of actions that can be performed in the current state of a payment.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  actions: Array<OrderAction>;
  /**
   * Maximum amount of money that can be captured.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  availableCaptureAmount?: Maybe<Money>;
  /**
   * Maximum amount of money that can be refunded.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  availableRefundAmount?: Maybe<Money>;
  /** Total amount captured for this payment. */
  capturedAmount?: Maybe<Money>;
  /** Internal payment status. */
  chargeStatus: PaymentChargeStatusEnum;
  checkout?: Maybe<Checkout>;
  created: Scalars['DateTime']['output'];
  /** The details of the card used for this payment. */
  creditCard?: Maybe<CreditCard>;
  /**
   * IP address of the user who created the payment.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  customerIpAddress?: Maybe<Scalars['String']['output']>;
  gateway: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  isActive: Scalars['Boolean']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  modified: Scalars['DateTime']['output'];
  order?: Maybe<Order>;
  paymentMethodType: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  token: Scalars['String']['output'];
  /** Total amount of the payment. */
  total?: Maybe<Money>;
  /**
   * List of all transactions within this payment.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  transactions?: Maybe<Array<Transaction>>;
};


/** Represents a payment of a given type. */
export type PaymentMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a payment of a given type. */
export type PaymentMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a payment of a given type. */
export type PaymentPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a payment of a given type. */
export type PaymentPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Authorize payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentAuthorize = Event & {
  __typename?: 'PaymentAuthorize';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Captures the authorized payment amount.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type PaymentCapture = {
  __typename?: 'PaymentCapture';
  errors: Array<PaymentError>;
  /** Updated payment. */
  payment?: Maybe<Payment>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

/**
 * Capture payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentCaptureEvent = Event & {
  __typename?: 'PaymentCaptureEvent';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum PaymentChargeStatusEnum {
  Cancelled = 'CANCELLED',
  FullyCharged = 'FULLY_CHARGED',
  FullyRefunded = 'FULLY_REFUNDED',
  NotCharged = 'NOT_CHARGED',
  PartiallyCharged = 'PARTIALLY_CHARGED',
  PartiallyRefunded = 'PARTIALLY_REFUNDED',
  Pending = 'PENDING',
  Refused = 'REFUSED'
}

/** Check payment balance. */
export type PaymentCheckBalance = {
  __typename?: 'PaymentCheckBalance';
  /** Response from the gateway. */
  data?: Maybe<Scalars['JSONString']['output']>;
  errors: Array<PaymentError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

export type PaymentCheckBalanceInput = {
  /** Information about card. */
  card: CardInput;
  /** Slug of a channel for which the data should be returned. */
  channel: Scalars['String']['input'];
  /** An ID of a payment gateway to check. */
  gatewayId: Scalars['String']['input'];
  /** Payment method name. */
  method: Scalars['String']['input'];
};

/**
 * Confirm payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentConfirmEvent = Event & {
  __typename?: 'PaymentConfirmEvent';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type PaymentCountableConnection = {
  __typename?: 'PaymentCountableConnection';
  edges: Array<PaymentCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type PaymentCountableEdge = {
  __typename?: 'PaymentCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Payment;
};

export type PaymentError = {
  __typename?: 'PaymentError';
  /** The error code. */
  code: PaymentErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of variant IDs which causes the error. */
  variants?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum PaymentErrorCode {
  BalanceCheckError = 'BALANCE_CHECK_ERROR',
  BillingAddressNotSet = 'BILLING_ADDRESS_NOT_SET',
  ChannelInactive = 'CHANNEL_INACTIVE',
  CheckoutEmailNotSet = 'CHECKOUT_EMAIL_NOT_SET',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidShippingMethod = 'INVALID_SHIPPING_METHOD',
  NotFound = 'NOT_FOUND',
  NotSupportedGateway = 'NOT_SUPPORTED_GATEWAY',
  NoCheckoutLines = 'NO_CHECKOUT_LINES',
  PartialPaymentNotAllowed = 'PARTIAL_PAYMENT_NOT_ALLOWED',
  PaymentError = 'PAYMENT_ERROR',
  Required = 'REQUIRED',
  ShippingAddressNotSet = 'SHIPPING_ADDRESS_NOT_SET',
  ShippingMethodNotSet = 'SHIPPING_METHOD_NOT_SET',
  UnavailableVariantInChannel = 'UNAVAILABLE_VARIANT_IN_CHANNEL',
  Unique = 'UNIQUE'
}

export type PaymentFilterInput = {
  checkouts?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Filter by ids.
   *
   * Added in Saleor 3.8.
   */
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/** Available payment gateway backend with configuration necessary to setup client. */
export type PaymentGateway = {
  __typename?: 'PaymentGateway';
  /** Payment gateway client configuration. */
  config: Array<GatewayConfigLine>;
  /** Payment gateway supported currencies. */
  currencies: Array<Scalars['String']['output']>;
  /** Payment gateway ID. */
  id: Scalars['ID']['output'];
  /** Payment gateway name. */
  name: Scalars['String']['output'];
};

export type PaymentGatewayConfig = {
  __typename?: 'PaymentGatewayConfig';
  /** The JSON data required to initialize the payment gateway. */
  data?: Maybe<Scalars['JSON']['output']>;
  errors?: Maybe<Array<PaymentGatewayConfigError>>;
  /** The app identifier. */
  id: Scalars['String']['output'];
};

export type PaymentGatewayConfigError = {
  __typename?: 'PaymentGatewayConfigError';
  /** The error code. */
  code: PaymentGatewayConfigErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum PaymentGatewayConfigErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

/**
 * Initializes a payment gateway session. It triggers the webhook `PAYMENT_GATEWAY_INITIALIZE_SESSION`, to the requested `paymentGateways`. If `paymentGateways` is not provided, the webhook will be send to all subscribed payment gateways.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type PaymentGatewayInitialize = {
  __typename?: 'PaymentGatewayInitialize';
  errors: Array<PaymentGatewayInitializeError>;
  gatewayConfigs?: Maybe<Array<PaymentGatewayConfig>>;
};

export type PaymentGatewayInitializeError = {
  __typename?: 'PaymentGatewayInitializeError';
  /** The error code. */
  code: PaymentGatewayInitializeErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum PaymentGatewayInitializeErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

/**
 * Event sent when user wants to initialize the payment gateway.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type PaymentGatewayInitializeSession = Event & {
  __typename?: 'PaymentGatewayInitializeSession';
  /** Amount requested for initializing the payment gateway. */
  amount?: Maybe<Scalars['PositiveDecimal']['output']>;
  /** Payment gateway data in JSON format, recieved from storefront. */
  data?: Maybe<Scalars['JSON']['output']>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Checkout or order */
  sourceObject: OrderOrCheckout;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type PaymentGatewayToInitialize = {
  /** The data that will be passed to the payment gateway. */
  data?: InputMaybe<Scalars['JSON']['input']>;
  /** The identifier of the payment gateway app to initialize. */
  id: Scalars['String']['input'];
};

/** Initializes payment process when it is required by gateway. */
export type PaymentInitialize = {
  __typename?: 'PaymentInitialize';
  errors: Array<PaymentError>;
  initializedPayment?: Maybe<PaymentInitialized>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

/** Server-side data generated by a payment gateway. Optional step when the payment provider requires an additional action to initialize payment session. */
export type PaymentInitialized = {
  __typename?: 'PaymentInitialized';
  /** Initialized data by gateway. */
  data?: Maybe<Scalars['JSONString']['output']>;
  /** ID of a payment gateway. */
  gateway: Scalars['String']['output'];
  /** Payment gateway name. */
  name: Scalars['String']['output'];
};

export type PaymentInput = {
  /** Total amount of the transaction, including all taxes and discounts. If no amount is provided, the checkout total will be used. */
  amount?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** A gateway to use with that payment. */
  gateway: Scalars['String']['input'];
  /**
   * User public metadata.
   *
   * Added in Saleor 3.1.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** URL of a storefront view where user should be redirected after requiring additional actions. Payment with additional actions will not be finished if this field is not provided. */
  returnUrl?: InputMaybe<Scalars['String']['input']>;
  /**
   * Payment store type.
   *
   * Added in Saleor 3.1.
   */
  storePaymentMethod?: InputMaybe<StorePaymentMethodEnum>;
  /** Client-side generated payment token, representing customer's billing data in a secure manner. */
  token?: InputMaybe<Scalars['String']['input']>;
};

/**
 * List payment gateways.
 *
 * Added in Saleor 3.6.
 */
export type PaymentListGateways = Event & {
  __typename?: 'PaymentListGateways';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Process payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentProcessEvent = Event & {
  __typename?: 'PaymentProcessEvent';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Refunds the captured payment amount.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type PaymentRefund = {
  __typename?: 'PaymentRefund';
  errors: Array<PaymentError>;
  /** Updated payment. */
  payment?: Maybe<Payment>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

/**
 * Refund payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentRefundEvent = Event & {
  __typename?: 'PaymentRefundEvent';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents a payment source stored for user in payment gateway, such as credit card. */
export type PaymentSource = {
  __typename?: 'PaymentSource';
  /** Stored credit card details if available. */
  creditCardInfo?: Maybe<CreditCard>;
  /** Payment gateway name. */
  gateway: Scalars['String']['output'];
  /**
   * List of public metadata items.
   *
   * Added in Saleor 3.1.
   *
   * Can be accessed without permissions.
   */
  metadata: Array<MetadataItem>;
  /** ID of stored payment method. */
  paymentMethodId?: Maybe<Scalars['String']['output']>;
};

/**
 * Voids the authorized payment.
 *
 * Requires one of the following permissions: MANAGE_ORDERS.
 */
export type PaymentVoid = {
  __typename?: 'PaymentVoid';
  errors: Array<PaymentError>;
  /** Updated payment. */
  payment?: Maybe<Payment>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  paymentErrors: Array<PaymentError>;
};

/**
 * Void payment.
 *
 * Added in Saleor 3.6.
 */
export type PaymentVoidEvent = Event & {
  __typename?: 'PaymentVoidEvent';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Look up a payment. */
  payment?: Maybe<Payment>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Represents a permission object in a friendly form. */
export type Permission = {
  __typename?: 'Permission';
  /** Internal code for permission. */
  code: PermissionEnum;
  /** Describe action(s) allowed to do by permission. */
  name: Scalars['String']['output'];
};

/** An enumeration. */
export enum PermissionEnum {
  HandleCheckouts = 'HANDLE_CHECKOUTS',
  HandlePayments = 'HANDLE_PAYMENTS',
  HandleTaxes = 'HANDLE_TAXES',
  ImpersonateUser = 'IMPERSONATE_USER',
  ManageApps = 'MANAGE_APPS',
  ManageChannels = 'MANAGE_CHANNELS',
  ManageCheckouts = 'MANAGE_CHECKOUTS',
  ManageDiscounts = 'MANAGE_DISCOUNTS',
  ManageGiftCard = 'MANAGE_GIFT_CARD',
  ManageMenus = 'MANAGE_MENUS',
  ManageObservability = 'MANAGE_OBSERVABILITY',
  ManageOrders = 'MANAGE_ORDERS',
  ManagePages = 'MANAGE_PAGES',
  ManagePageTypesAndAttributes = 'MANAGE_PAGE_TYPES_AND_ATTRIBUTES',
  ManagePlugins = 'MANAGE_PLUGINS',
  ManageProducts = 'MANAGE_PRODUCTS',
  ManageProductTypesAndAttributes = 'MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES',
  ManageSettings = 'MANAGE_SETTINGS',
  ManageShipping = 'MANAGE_SHIPPING',
  ManageStaff = 'MANAGE_STAFF',
  ManageTaxes = 'MANAGE_TAXES',
  ManageTranslations = 'MANAGE_TRANSLATIONS',
  ManageUsers = 'MANAGE_USERS'
}

/**
 * Create new permission group. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type PermissionGroupCreate = {
  __typename?: 'PermissionGroupCreate';
  errors: Array<PermissionGroupError>;
  group?: Maybe<Group>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  permissionGroupErrors: Array<PermissionGroupError>;
};

export type PermissionGroupCreateInput = {
  /**
   * List of channels to assign to this group.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  addChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of permission code names to assign to this group. */
  addPermissions?: InputMaybe<Array<PermissionEnum>>;
  /** List of users to assign to this group. */
  addUsers?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Group name. */
  name: Scalars['String']['input'];
  /**
   * Determine if the group has restricted access to channels.  DEFAULT: False
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  restrictedAccessToChannels?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Event sent when new permission group is created.
 *
 * Added in Saleor 3.6.
 */
export type PermissionGroupCreated = Event & {
  __typename?: 'PermissionGroupCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The permission group the event relates to. */
  permissionGroup?: Maybe<Group>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Delete permission group. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type PermissionGroupDelete = {
  __typename?: 'PermissionGroupDelete';
  errors: Array<PermissionGroupError>;
  group?: Maybe<Group>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  permissionGroupErrors: Array<PermissionGroupError>;
};

/**
 * Event sent when permission group is deleted.
 *
 * Added in Saleor 3.6.
 */
export type PermissionGroupDeleted = Event & {
  __typename?: 'PermissionGroupDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The permission group the event relates to. */
  permissionGroup?: Maybe<Group>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type PermissionGroupError = {
  __typename?: 'PermissionGroupError';
  /** List of chnnels IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: PermissionGroupErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of permissions which causes the error. */
  permissions?: Maybe<Array<PermissionEnum>>;
  /** List of user IDs which causes the error. */
  users?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum PermissionGroupErrorCode {
  AssignNonStaffMember = 'ASSIGN_NON_STAFF_MEMBER',
  CannotRemoveFromLastGroup = 'CANNOT_REMOVE_FROM_LAST_GROUP',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  LeftNotManageablePermission = 'LEFT_NOT_MANAGEABLE_PERMISSION',
  OutOfScopeChannel = 'OUT_OF_SCOPE_CHANNEL',
  OutOfScopePermission = 'OUT_OF_SCOPE_PERMISSION',
  OutOfScopeUser = 'OUT_OF_SCOPE_USER',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type PermissionGroupFilterInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  search?: InputMaybe<Scalars['String']['input']>;
};

/** Sorting options for permission groups. */
export enum PermissionGroupSortField {
  /** Sort permission group accounts by name. */
  Name = 'NAME'
}

export type PermissionGroupSortingInput = {
  /** Specifies the direction in which to sort permission group. */
  direction: OrderDirection;
  /** Sort permission group by the selected field. */
  field: PermissionGroupSortField;
};

/**
 * Update permission group. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type PermissionGroupUpdate = {
  __typename?: 'PermissionGroupUpdate';
  errors: Array<PermissionGroupError>;
  group?: Maybe<Group>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  permissionGroupErrors: Array<PermissionGroupError>;
};

export type PermissionGroupUpdateInput = {
  /**
   * List of channels to assign to this group.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  addChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of permission code names to assign to this group. */
  addPermissions?: InputMaybe<Array<PermissionEnum>>;
  /** List of users to assign to this group. */
  addUsers?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Group name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * List of channels to unassign from this group.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of permission code names to unassign from this group. */
  removePermissions?: InputMaybe<Array<PermissionEnum>>;
  /** List of users to unassign from this group. */
  removeUsers?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Determine if the group has restricted access to channels.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  restrictedAccessToChannels?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Event sent when permission group is updated.
 *
 * Added in Saleor 3.6.
 */
export type PermissionGroupUpdated = Event & {
  __typename?: 'PermissionGroupUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The permission group the event relates to. */
  permissionGroup?: Maybe<Group>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Plugin. */
export type Plugin = {
  __typename?: 'Plugin';
  /** Channel-specific plugin configuration. */
  channelConfigurations: Array<PluginConfiguration>;
  /** Description of the plugin. */
  description: Scalars['String']['output'];
  /** Global configuration of the plugin (not channel-specific). */
  globalConfiguration?: Maybe<PluginConfiguration>;
  /** Identifier of the plugin. */
  id: Scalars['ID']['output'];
  /** Name of the plugin. */
  name: Scalars['String']['output'];
};

/** Stores information about a configuration of plugin. */
export type PluginConfiguration = {
  __typename?: 'PluginConfiguration';
  /** Determines if plugin is active or not. */
  active: Scalars['Boolean']['output'];
  /** The channel to which the plugin configuration is assigned to. */
  channel?: Maybe<Channel>;
  /** Configuration of the plugin. */
  configuration?: Maybe<Array<ConfigurationItem>>;
};

export enum PluginConfigurationType {
  Global = 'GLOBAL',
  PerChannel = 'PER_CHANNEL'
}

export type PluginCountableConnection = {
  __typename?: 'PluginCountableConnection';
  edges: Array<PluginCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type PluginCountableEdge = {
  __typename?: 'PluginCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Plugin;
};

export type PluginError = {
  __typename?: 'PluginError';
  /** The error code. */
  code: PluginErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum PluginErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  PluginMisconfigured = 'PLUGIN_MISCONFIGURED',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type PluginFilterInput = {
  search?: InputMaybe<Scalars['String']['input']>;
  statusInChannels?: InputMaybe<PluginStatusInChannelsInput>;
  type?: InputMaybe<PluginConfigurationType>;
};

export enum PluginSortField {
  IsActive = 'IS_ACTIVE',
  Name = 'NAME'
}

export type PluginSortingInput = {
  /** Specifies the direction in which to sort plugins. */
  direction: OrderDirection;
  /** Sort plugins by the selected field. */
  field: PluginSortField;
};

export type PluginStatusInChannelsInput = {
  active: Scalars['Boolean']['input'];
  channels: Array<Scalars['ID']['input']>;
};

/**
 * Update plugin configuration.
 *
 * Requires one of the following permissions: MANAGE_PLUGINS.
 */
export type PluginUpdate = {
  __typename?: 'PluginUpdate';
  errors: Array<PluginError>;
  plugin?: Maybe<Plugin>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  pluginsErrors: Array<PluginError>;
};

export type PluginUpdateInput = {
  /** Indicates whether the plugin should be enabled. */
  active?: InputMaybe<Scalars['Boolean']['input']>;
  /** Configuration of the plugin. */
  configuration?: InputMaybe<Array<ConfigurationItemInput>>;
};

/** An enumeration. */
export enum PostalCodeRuleInclusionTypeEnum {
  Exclude = 'EXCLUDE',
  Include = 'INCLUDE'
}

/** Represents preorder settings for product variant. */
export type PreorderData = {
  __typename?: 'PreorderData';
  /** Preorder end date. */
  endDate?: Maybe<Scalars['DateTime']['output']>;
  /**
   * Total number of sold product variant during preorder.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  globalSoldUnits: Scalars['Int']['output'];
  /**
   * The global preorder threshold for product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  globalThreshold?: Maybe<Scalars['Int']['output']>;
};

export type PreorderSettingsInput = {
  /** The end date for preorder. */
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** The global threshold for preorder variant. */
  globalThreshold?: InputMaybe<Scalars['Int']['input']>;
};

/** Represents preorder variant data for channel. */
export type PreorderThreshold = {
  __typename?: 'PreorderThreshold';
  /** Preorder threshold for product variant in this channel. */
  quantity?: Maybe<Scalars['Int']['output']>;
  /** Number of sold product variant in this channel. */
  soldUnits: Scalars['Int']['output'];
};

export type PriceInput = {
  /** Amount of money. */
  amount: Scalars['PositiveDecimal']['input'];
  /** Currency code. */
  currency: Scalars['String']['input'];
};

export type PriceRangeInput = {
  /** Price greater than or equal to. */
  gte?: InputMaybe<Scalars['Float']['input']>;
  /** Price less than or equal to. */
  lte?: InputMaybe<Scalars['Float']['input']>;
};

/** Represents an individual item for sale in the storefront. */
export type Product = Node & ObjectWithMetadata & {
  __typename?: 'Product';
  /**
   * Get a single attribute attached to product by attribute slug.
   *
   * Added in Saleor 3.9.
   */
  attribute?: Maybe<SelectedAttribute>;
  /** List of attributes assigned to this product. */
  attributes: Array<SelectedAttribute>;
  /**
   * Date when product is available for purchase.
   * @deprecated This field will be removed in Saleor 4.0. Use the `availableForPurchaseAt` field to fetch the available for purchase date.
   */
  availableForPurchase?: Maybe<Scalars['Date']['output']>;
  /** Date when product is available for purchase. */
  availableForPurchaseAt?: Maybe<Scalars['DateTime']['output']>;
  category?: Maybe<Category>;
  /** Channel given to retrieve this product. Also used by federation gateway to resolve this object in a federated query. */
  channel?: Maybe<Scalars['String']['output']>;
  /**
   * List of availability in channels for the product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  channelListings?: Maybe<Array<ProductChannelListing>>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `Channel.taxConfiguration` field to determine whether tax collection is enabled. */
  chargeTaxes: Scalars['Boolean']['output'];
  /** List of collections for the product. Requires the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  collections?: Maybe<Array<Collection>>;
  created: Scalars['DateTime']['output'];
  defaultVariant?: Maybe<ProductVariant>;
  /**
   * Description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  /**
   * External ID of this product.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /**
   * Get a single product image by ID.
   * @deprecated This field will be removed in Saleor 4.0. Use the `mediaById` field instead.
   */
  imageById?: Maybe<ProductImage>;
  /**
   * List of images for the product.
   * @deprecated This field will be removed in Saleor 4.0. Use the `media` field instead.
   */
  images?: Maybe<Array<ProductImage>>;
  /** Whether the product is in stock and visible or not. */
  isAvailable?: Maybe<Scalars['Boolean']['output']>;
  /** Whether the product is available for purchase. */
  isAvailableForPurchase?: Maybe<Scalars['Boolean']['output']>;
  /** List of media for the product. */
  media?: Maybe<Array<ProductMedia>>;
  /** Get a single product media by ID. */
  mediaById?: Maybe<ProductMedia>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** Lists the storefront product's pricing, the current price and discounts, only meant for displaying. */
  pricing?: Maybe<ProductPricingInfo>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  productType: ProductType;
  rating?: Maybe<Scalars['Float']['output']>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  slug: Scalars['String']['output'];
  /**
   * Tax class assigned to this product type. All products of this product type use this tax class, unless it's overridden in the `Product` type.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClass?: Maybe<TaxClass>;
  /**
   * A type of tax. Assigned by enabled tax gateway
   * @deprecated This field will be removed in Saleor 4.0. Use `taxClass` field instead.
   */
  taxType?: Maybe<TaxType>;
  thumbnail?: Maybe<Image>;
  /** Returns translated product fields for the given language code. */
  translation?: Maybe<ProductTranslation>;
  updatedAt: Scalars['DateTime']['output'];
  /**
   * Get a single variant by SKU or ID.
   *
   * Added in Saleor 3.9.
   * @deprecated This field will be removed in Saleor 4.0. Use top-level `variant` query.
   */
  variant?: Maybe<ProductVariant>;
  /** List of variants for the product. Requires the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  variants?: Maybe<Array<ProductVariant>>;
  weight?: Maybe<Weight>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductAttributeArgs = {
  slug: Scalars['String']['input'];
};


/** Represents an individual item for sale in the storefront. */
export type ProductImageByIdArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductIsAvailableArgs = {
  address?: InputMaybe<AddressInput>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductMediaArgs = {
  sortBy?: InputMaybe<MediaSortingInput>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductMediaByIdArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an individual item for sale in the storefront. */
export type ProductMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductPricingArgs = {
  address?: InputMaybe<AddressInput>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents an individual item for sale in the storefront. */
export type ProductPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductThumbnailArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents an individual item for sale in the storefront. */
export type ProductTranslationArgs = {
  languageCode: LanguageCodeEnum;
};


/** Represents an individual item for sale in the storefront. */
export type ProductVariantArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Assign attributes to a given product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductAttributeAssign = {
  __typename?: 'ProductAttributeAssign';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  /** The updated product type. */
  productType?: Maybe<ProductType>;
};

export type ProductAttributeAssignInput = {
  /** The ID of the attribute to assign. */
  id: Scalars['ID']['input'];
  /** The attribute type to be assigned as. */
  type: ProductAttributeType;
  /**
   * Whether attribute is allowed in variant selection. Allowed types are: ['dropdown', 'boolean', 'swatch', 'numeric'].
   *
   * Added in Saleor 3.1.
   */
  variantSelection?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Update attributes assigned to product variant for given product type.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductAttributeAssignmentUpdate = {
  __typename?: 'ProductAttributeAssignmentUpdate';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  /** The updated product type. */
  productType?: Maybe<ProductType>;
};

export type ProductAttributeAssignmentUpdateInput = {
  /** The ID of the attribute to assign. */
  id: Scalars['ID']['input'];
  /**
   * Whether attribute is allowed in variant selection. Allowed types are: ['dropdown', 'boolean', 'swatch', 'numeric'].
   *
   * Added in Saleor 3.1.
   */
  variantSelection: Scalars['Boolean']['input'];
};

export enum ProductAttributeType {
  Product = 'PRODUCT',
  Variant = 'VARIANT'
}

/**
 * Un-assign attributes from a given product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductAttributeUnassign = {
  __typename?: 'ProductAttributeUnassign';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  /** The updated product type. */
  productType?: Maybe<ProductType>;
};

/**
 * Creates products.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductBulkCreate = {
  __typename?: 'ProductBulkCreate';
  /** Returns how many objects were created. */
  count: Scalars['Int']['output'];
  errors: Array<ProductBulkCreateError>;
  /** List of the created products. */
  results: Array<ProductBulkResult>;
};

export type ProductBulkCreateError = {
  __typename?: 'ProductBulkCreateError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of channel IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductBulkCreateErrorCode;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** Path to field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  path?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of warehouse IDs which causes the error. */
  warehouses?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum ProductBulkCreateErrorCode {
  AttributeAlreadyAssigned = 'ATTRIBUTE_ALREADY_ASSIGNED',
  AttributeCannotBeAssigned = 'ATTRIBUTE_CANNOT_BE_ASSIGNED',
  AttributeVariantsDisabled = 'ATTRIBUTE_VARIANTS_DISABLED',
  Blank = 'BLANK',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidPrice = 'INVALID_PRICE',
  MaxLength = 'MAX_LENGTH',
  NotFound = 'NOT_FOUND',
  ProductNotAssignedToChannel = 'PRODUCT_NOT_ASSIGNED_TO_CHANNEL',
  ProductWithoutCategory = 'PRODUCT_WITHOUT_CATEGORY',
  Required = 'REQUIRED',
  Unique = 'UNIQUE',
  UnsupportedMediaProvider = 'UNSUPPORTED_MEDIA_PROVIDER'
}

export type ProductBulkCreateInput = {
  /** List of attributes. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /** ID of the product's category. */
  category?: InputMaybe<Scalars['ID']['input']>;
  /** List of channels in which the product is available. */
  channelListings?: InputMaybe<Array<ProductChannelListingCreateInput>>;
  /**
   * Determine if taxes are being charged for the product.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `Channel.taxConfiguration` to configure whether tax collection is enabled.
   */
  chargeTaxes?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of IDs of collections that the product belongs to. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Product description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /** External ID of this product. */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** List of media inputs associated with the product. */
  media?: InputMaybe<Array<MediaInput>>;
  /** Fields required to update the product metadata. */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Product name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Fields required to update the product private metadata. */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** ID of the type that product belongs to. */
  productType: Scalars['ID']['input'];
  /** Defines the product rating value. */
  rating?: InputMaybe<Scalars['Float']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Product slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** ID of a tax class to assign to this product. If not provided, product will use the tax class which is assigned to the product type. */
  taxClass?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Tax rate for enabled tax gateway.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use tax classes to control the tax calculation for a product. If taxCode is provided, Saleor will try to find a tax class with given code (codes are stored in metadata) and assign it. If no tax class is found, it would be created and assigned.
   */
  taxCode?: InputMaybe<Scalars['String']['input']>;
  /** Input list of product variants to create. */
  variants?: InputMaybe<Array<ProductVariantBulkCreateInput>>;
  /** Weight of the Product. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/**
 * Deletes products.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductBulkDelete = {
  __typename?: 'ProductBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductBulkResult = {
  __typename?: 'ProductBulkResult';
  /** List of errors occurred on create attempt. */
  errors?: Maybe<Array<ProductBulkCreateError>>;
  /** Product data. */
  product?: Maybe<Product>;
};

/** Represents product channel listing. */
export type ProductChannelListing = Node & {
  __typename?: 'ProductChannelListing';
  /** @deprecated This field will be removed in Saleor 4.0. Use the `availableForPurchaseAt` field to fetch the available for purchase date. */
  availableForPurchase?: Maybe<Scalars['Date']['output']>;
  /**
   * The product available for purchase date time.
   *
   * Added in Saleor 3.3.
   */
  availableForPurchaseAt?: Maybe<Scalars['DateTime']['output']>;
  channel: Channel;
  /** The price of the cheapest variant (including discounts). */
  discountedPrice?: Maybe<Money>;
  id: Scalars['ID']['output'];
  /** Whether the product is available for purchase. */
  isAvailableForPurchase?: Maybe<Scalars['Boolean']['output']>;
  isPublished: Scalars['Boolean']['output'];
  /**
   * Range of margin percentage value.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  margin?: Maybe<Margin>;
  /** Lists the storefront product's pricing, the current price and discounts, only meant for displaying. */
  pricing?: Maybe<ProductPricingInfo>;
  /** @deprecated This field will be removed in Saleor 4.0. Use the `publishedAt` field to fetch the publication date. */
  publicationDate?: Maybe<Scalars['Date']['output']>;
  /**
   * The product publication date time.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  /**
   * Purchase cost of product.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  purchaseCost?: Maybe<MoneyRange>;
  visibleInListings: Scalars['Boolean']['output'];
};


/** Represents product channel listing. */
export type ProductChannelListingPricingArgs = {
  address?: InputMaybe<AddressInput>;
};

export type ProductChannelListingAddInput = {
  /** List of variants to which the channel should be assigned. */
  addVariants?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * A start date time from which a product will be available for purchase. When not set and `isAvailable` is set to True, the current day is assumed.
   *
   * Added in Saleor 3.3.
   */
  availableForPurchaseAt?: InputMaybe<Scalars['DateTime']['input']>;
  /**
   * A start date from which a product will be available for purchase. When not set and isAvailable is set to True, the current day is assumed.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `availableForPurchaseAt` field instead.
   */
  availableForPurchaseDate?: InputMaybe<Scalars['Date']['input']>;
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Determine if product should be available for purchase. */
  isAvailableForPurchase?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if object is visible to customers. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `publishedAt` field instead.
   */
  publicationDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * Publication date time. ISO 8601 standard.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** List of variants from which the channel should be unassigned. */
  removeVariants?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Determines if product is visible in product listings (doesn't apply to product collections). */
  visibleInListings?: InputMaybe<Scalars['Boolean']['input']>;
};

export type ProductChannelListingCreateInput = {
  /** A start date time from which a product will be available for purchase. When not set and `isAvailable` is set to True, the current day is assumed. */
  availableForPurchaseAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Determine if product should be available for purchase. */
  isAvailableForPurchase?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if object is visible to customers. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /** Publication date time. ISO 8601 standard. */
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** Determines if product is visible in product listings (doesn't apply to product collections). */
  visibleInListings?: InputMaybe<Scalars['Boolean']['input']>;
};

export type ProductChannelListingError = {
  __typename?: 'ProductChannelListingError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of channels IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of variants IDs which causes the error. */
  variants?: Maybe<Array<Scalars['ID']['output']>>;
};

/**
 * Manage product's availability in channels.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductChannelListingUpdate = {
  __typename?: 'ProductChannelListingUpdate';
  errors: Array<ProductChannelListingError>;
  /** An updated product instance. */
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productChannelListingErrors: Array<ProductChannelListingError>;
};

export type ProductChannelListingUpdateInput = {
  /** List of channels from which the product should be unassigned. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of channels to which the product should be assigned or updated. */
  updateChannels?: InputMaybe<Array<ProductChannelListingAddInput>>;
};

export type ProductCountableConnection = {
  __typename?: 'ProductCountableConnection';
  edges: Array<ProductCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type ProductCountableEdge = {
  __typename?: 'ProductCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Product;
};

/**
 * Creates a new product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductCreate = {
  __typename?: 'ProductCreate';
  errors: Array<ProductError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductCreateInput = {
  /** List of attributes. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /** ID of the product's category. */
  category?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Determine if taxes are being charged for the product.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `Channel.taxConfiguration` to configure whether tax collection is enabled.
   */
  chargeTaxes?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of IDs of collections that the product belongs to. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Product description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * External ID of this product.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Product name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** ID of the type that product belongs to. */
  productType: Scalars['ID']['input'];
  /** Defines the product rating value. */
  rating?: InputMaybe<Scalars['Float']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Product slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** ID of a tax class to assign to this product. If not provided, product will use the tax class which is assigned to the product type. */
  taxClass?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Tax rate for enabled tax gateway.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use tax classes to control the tax calculation for a product. If taxCode is provided, Saleor will try to find a tax class with given code (codes are stored in metadata) and assign it. If no tax class is found, it would be created and assigned.
   */
  taxCode?: InputMaybe<Scalars['String']['input']>;
  /** Weight of the Product. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/**
 * Event sent when new product is created.
 *
 * Added in Saleor 3.2.
 */
export type ProductCreated = Event & {
  __typename?: 'ProductCreated';
  /** The category of the product. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product the event relates to. */
  product?: Maybe<Product>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new product is created.
 *
 * Added in Saleor 3.2.
 */
export type ProductCreatedProductArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductDelete = {
  __typename?: 'ProductDelete';
  errors: Array<ProductError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when product is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ProductDeleted = Event & {
  __typename?: 'ProductDeleted';
  /** The category of the product. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product the event relates to. */
  product?: Maybe<Product>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ProductDeletedProductArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type ProductError = {
  __typename?: 'ProductError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum ProductErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  AttributeAlreadyAssigned = 'ATTRIBUTE_ALREADY_ASSIGNED',
  AttributeCannotBeAssigned = 'ATTRIBUTE_CANNOT_BE_ASSIGNED',
  AttributeVariantsDisabled = 'ATTRIBUTE_VARIANTS_DISABLED',
  CannotManageProductWithoutVariant = 'CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidPrice = 'INVALID_PRICE',
  MediaAlreadyAssigned = 'MEDIA_ALREADY_ASSIGNED',
  NotFound = 'NOT_FOUND',
  NotProductsImage = 'NOT_PRODUCTS_IMAGE',
  NotProductsVariant = 'NOT_PRODUCTS_VARIANT',
  PreorderVariantCannotBeDeactivated = 'PREORDER_VARIANT_CANNOT_BE_DEACTIVATED',
  ProductNotAssignedToChannel = 'PRODUCT_NOT_ASSIGNED_TO_CHANNEL',
  ProductWithoutCategory = 'PRODUCT_WITHOUT_CATEGORY',
  Required = 'REQUIRED',
  Unique = 'UNIQUE',
  UnsupportedMediaProvider = 'UNSUPPORTED_MEDIA_PROVIDER',
  VariantNoDigitalContent = 'VARIANT_NO_DIGITAL_CONTENT'
}

export enum ProductFieldEnum {
  Category = 'CATEGORY',
  ChargeTaxes = 'CHARGE_TAXES',
  Collections = 'COLLECTIONS',
  Description = 'DESCRIPTION',
  Name = 'NAME',
  ProductMedia = 'PRODUCT_MEDIA',
  ProductType = 'PRODUCT_TYPE',
  ProductWeight = 'PRODUCT_WEIGHT',
  VariantId = 'VARIANT_ID',
  VariantMedia = 'VARIANT_MEDIA',
  VariantSku = 'VARIANT_SKU',
  VariantWeight = 'VARIANT_WEIGHT'
}

export type ProductFilterInput = {
  attributes?: InputMaybe<Array<AttributeInput>>;
  /**
   * Filter by the date of availability for purchase.
   *
   * Added in Saleor 3.8.
   */
  availableFrom?: InputMaybe<Scalars['DateTime']['input']>;
  categories?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Specifies the channel by which the data should be filtered.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Filter on whether product is a gift card or not. */
  giftCard?: InputMaybe<Scalars['Boolean']['input']>;
  hasCategory?: InputMaybe<Scalars['Boolean']['input']>;
  hasPreorderedVariants?: InputMaybe<Scalars['Boolean']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Filter by availability for purchase.
   *
   * Added in Saleor 3.8.
   */
  isAvailable?: InputMaybe<Scalars['Boolean']['input']>;
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Filter by visibility in product listings.
   *
   * Added in Saleor 3.8.
   */
  isVisibleInListing?: InputMaybe<Scalars['Boolean']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  /** Filter by the lowest variant price after discounts. */
  minimalPrice?: InputMaybe<PriceRangeInput>;
  price?: InputMaybe<PriceRangeInput>;
  productTypes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Filter by the publication date.
   *
   * Added in Saleor 3.8.
   */
  publishedFrom?: InputMaybe<Scalars['DateTime']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
  /** Filter by variants having specific stock status. */
  stockAvailability?: InputMaybe<StockAvailability>;
  stocks?: InputMaybe<ProductStockFilterInput>;
  /** Filter by when was the most recent update. */
  updatedAt?: InputMaybe<DateTimeRangeInput>;
};

/** Represents a product image. */
export type ProductImage = {
  __typename?: 'ProductImage';
  /** The alt text of the image. */
  alt?: Maybe<Scalars['String']['output']>;
  /** The ID of the image. */
  id: Scalars['ID']['output'];
  /** The new relative sorting position of the item (from -inf to +inf). 1 moves the item one position forward, -1 moves the item one position backward, 0 leaves the item unchanged. */
  sortOrder?: Maybe<Scalars['Int']['output']>;
  url: Scalars['String']['output'];
};


/** Represents a product image. */
export type ProductImageUrlArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};

export type ProductInput = {
  /** List of attributes. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /** ID of the product's category. */
  category?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Determine if taxes are being charged for the product.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `Channel.taxConfiguration` to configure whether tax collection is enabled.
   */
  chargeTaxes?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of IDs of collections that the product belongs to. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /**
   * Product description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * External ID of this product.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Product name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** Defines the product rating value. */
  rating?: InputMaybe<Scalars['Float']['input']>;
  /** Search engine optimization fields. */
  seo?: InputMaybe<SeoInput>;
  /** Product slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** ID of a tax class to assign to this product. If not provided, product will use the tax class which is assigned to the product type. */
  taxClass?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Tax rate for enabled tax gateway.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use tax classes to control the tax calculation for a product. If taxCode is provided, Saleor will try to find a tax class with given code (codes are stored in metadata) and assign it. If no tax class is found, it would be created and assigned.
   */
  taxCode?: InputMaybe<Scalars['String']['input']>;
  /** Weight of the Product. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/** Represents a product media. */
export type ProductMedia = Node & ObjectWithMetadata & {
  __typename?: 'ProductMedia';
  alt: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /**
   * List of public metadata items. Can be accessed without permissions.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  oembedData: Scalars['JSONString']['output'];
  /**
   * List of private metadata items. Requires staff permissions to access.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * Product id the media refers to.
   *
   * Added in Saleor 3.12.
   */
  productId?: Maybe<Scalars['ID']['output']>;
  sortOrder?: Maybe<Scalars['Int']['output']>;
  type: ProductMediaType;
  url: Scalars['String']['output'];
};


/** Represents a product media. */
export type ProductMediaMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a product media. */
export type ProductMediaMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a product media. */
export type ProductMediaPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a product media. */
export type ProductMediaPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a product media. */
export type ProductMediaUrlArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};

/**
 * Deletes product media.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductMediaBulkDelete = {
  __typename?: 'ProductMediaBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Create a media object (image or video URL) associated with product. For image, this mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductMediaCreate = {
  __typename?: 'ProductMediaCreate';
  errors: Array<ProductError>;
  media?: Maybe<ProductMedia>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductMediaCreateInput = {
  /** Alt text for a product media. */
  alt?: InputMaybe<Scalars['String']['input']>;
  /** Represents an image file in a multipart request. */
  image?: InputMaybe<Scalars['Upload']['input']>;
  /** Represents an URL to an external media. */
  mediaUrl?: InputMaybe<Scalars['String']['input']>;
  /** ID of an product. */
  product: Scalars['ID']['input'];
};

/**
 * Event sent when new product media is created.
 *
 * Added in Saleor 3.12.
 */
export type ProductMediaCreated = Event & {
  __typename?: 'ProductMediaCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product media the event relates to. */
  productMedia?: Maybe<ProductMedia>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a product media.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductMediaDelete = {
  __typename?: 'ProductMediaDelete';
  errors: Array<ProductError>;
  media?: Maybe<ProductMedia>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when product media is deleted.
 *
 * Added in Saleor 3.12.
 */
export type ProductMediaDeleted = Event & {
  __typename?: 'ProductMediaDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product media the event relates to. */
  productMedia?: Maybe<ProductMedia>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Changes ordering of the product media.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductMediaReorder = {
  __typename?: 'ProductMediaReorder';
  errors: Array<ProductError>;
  media?: Maybe<Array<ProductMedia>>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/** An enumeration. */
export enum ProductMediaType {
  Image = 'IMAGE',
  Video = 'VIDEO'
}

/**
 * Updates a product media.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductMediaUpdate = {
  __typename?: 'ProductMediaUpdate';
  errors: Array<ProductError>;
  media?: Maybe<ProductMedia>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductMediaUpdateInput = {
  /** Alt text for a product media. */
  alt?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when product media is updated.
 *
 * Added in Saleor 3.12.
 */
export type ProductMediaUpdated = Event & {
  __typename?: 'ProductMediaUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product media the event relates to. */
  productMedia?: Maybe<ProductMedia>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when product metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ProductMetadataUpdated = Event & {
  __typename?: 'ProductMetadataUpdated';
  /** The category of the product. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product the event relates to. */
  product?: Maybe<Product>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ProductMetadataUpdatedProductArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type ProductOrder = {
  /**
   * Sort product by the selected attribute's values.
   * Note: this doesn't take translations into account yet.
   */
  attributeId?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Specifies the channel in which to sort the data.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Specifies the direction in which to sort products. */
  direction: OrderDirection;
  /** Sort products by the selected field. */
  field?: InputMaybe<ProductOrderField>;
};

export enum ProductOrderField {
  /**
   * Sort products by collection. Note: This option is available only for the `Collection.products` query.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Collection = 'COLLECTION',
  /**
   * Sort products by creation date.
   *
   * Added in Saleor 3.8.
   */
  CreatedAt = 'CREATED_AT',
  /** Sort products by update date. */
  Date = 'DATE',
  /** Sort products by update date. */
  LastModified = 'LAST_MODIFIED',
  /** Sort products by update date. */
  LastModifiedAt = 'LAST_MODIFIED_AT',
  /**
   * Sort products by a minimal price of a product's variant.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  MinimalPrice = 'MINIMAL_PRICE',
  /** Sort products by name. */
  Name = 'NAME',
  /**
   * Sort products by price.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Price = 'PRICE',
  /**
   * Sort products by publication date.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  PublicationDate = 'PUBLICATION_DATE',
  /**
   * Sort products by publication status.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Published = 'PUBLISHED',
  /**
   * Sort products by publication date.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  PublishedAt = 'PUBLISHED_AT',
  /** Sort products by rank. Note: This option is available only with the `search` filter. */
  Rank = 'RANK',
  /** Sort products by rating. */
  Rating = 'RATING',
  /** Sort products by type. */
  Type = 'TYPE'
}

/** Represents availability of a product in the storefront. */
export type ProductPricingInfo = {
  __typename?: 'ProductPricingInfo';
  /** The discount amount if in sale (null otherwise). */
  discount?: Maybe<TaxedMoney>;
  /** The discount amount in the local currency. */
  discountLocalCurrency?: Maybe<TaxedMoney>;
  /**
   * Determines whether this product's price displayed in a storefront should include taxes.
   *
   * Added in Saleor 3.9.
   */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** Whether it is in sale or not. */
  onSale?: Maybe<Scalars['Boolean']['output']>;
  /** The discounted price range of the product variants. */
  priceRange?: Maybe<TaxedMoneyRange>;
  /** The discounted price range of the product variants in the local currency. */
  priceRangeLocalCurrency?: Maybe<TaxedMoneyRange>;
  /** The undiscounted price range of the product variants. */
  priceRangeUndiscounted?: Maybe<TaxedMoneyRange>;
};

/**
 * Reorder product attribute values.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductReorderAttributeValues = {
  __typename?: 'ProductReorderAttributeValues';
  errors: Array<ProductError>;
  /** Product from which attribute values are reordered. */
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductStockFilterInput = {
  quantity?: InputMaybe<IntRangeInput>;
  warehouseIds?: InputMaybe<Array<Scalars['ID']['input']>>;
};

export type ProductTranslatableContent = Node & {
  __typename?: 'ProductTranslatableContent';
  /** List of product attribute values that can be translated. */
  attributeValues: Array<AttributeValueTranslatableContent>;
  /**
   * Description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /**
   * Represents an individual item for sale in the storefront.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  product?: Maybe<Product>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
  /** Returns translated product fields for the given language code. */
  translation?: Maybe<ProductTranslation>;
};


export type ProductTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a product.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type ProductTranslate = {
  __typename?: 'ProductTranslate';
  errors: Array<TranslationError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type ProductTranslation = Node & {
  __typename?: 'ProductTranslation';
  /**
   * Translated description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * Translated description of the product.
   *
   * Rich text format. For reference see https://editorjs.io/
   * @deprecated This field will be removed in Saleor 4.0. Use the `description` field instead.
   */
  descriptionJson?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
  seoDescription?: Maybe<Scalars['String']['output']>;
  seoTitle?: Maybe<Scalars['String']['output']>;
};

/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductType = Node & ObjectWithMetadata & {
  __typename?: 'ProductType';
  /**
   * Variant attributes of that product type with attached variant selection.
   *
   * Added in Saleor 3.1.
   */
  assignedVariantAttributes?: Maybe<Array<AssignedVariantAttribute>>;
  /**
   * List of attributes which can be assigned to this product type.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  availableAttributes?: Maybe<AttributeCountableConnection>;
  hasVariants: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  isDigital: Scalars['Boolean']['output'];
  isShippingRequired: Scalars['Boolean']['output'];
  /** The product type kind. */
  kind: ProductTypeKindEnum;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Product attributes of that product type. */
  productAttributes?: Maybe<Array<Attribute>>;
  /**
   * List of products of this type.
   * @deprecated This field will be removed in Saleor 4.0. Use the top-level `products` query with the `productTypes` filter.
   */
  products?: Maybe<ProductCountableConnection>;
  slug: Scalars['String']['output'];
  /**
   * Tax class assigned to this product type. All products of this product type use this tax class, unless it's overridden in the `Product` type.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClass?: Maybe<TaxClass>;
  /**
   * A type of tax. Assigned by enabled tax gateway
   * @deprecated This field will be removed in Saleor 4.0. Use `taxClass` field instead.
   */
  taxType?: Maybe<TaxType>;
  /**
   * Variant attributes of that product type.
   * @deprecated This field will be removed in Saleor 4.0. Use `assignedVariantAttributes` instead.
   */
  variantAttributes?: Maybe<Array<Attribute>>;
  weight?: Maybe<Weight>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeAssignedVariantAttributesArgs = {
  variantSelection?: InputMaybe<VariantAttributeScope>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeAvailableAttributesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AttributeFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  where?: InputMaybe<AttributeWhereInput>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents a type of product. It defines what attributes are available to products of this type. */
export type ProductTypeVariantAttributesArgs = {
  variantSelection?: InputMaybe<VariantAttributeScope>;
};

/**
 * Deletes product types.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductTypeBulkDelete = {
  __typename?: 'ProductTypeBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export enum ProductTypeConfigurable {
  Configurable = 'CONFIGURABLE',
  Simple = 'SIMPLE'
}

export type ProductTypeCountableConnection = {
  __typename?: 'ProductTypeCountableConnection';
  edges: Array<ProductTypeCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type ProductTypeCountableEdge = {
  __typename?: 'ProductTypeCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: ProductType;
};

/**
 * Creates a new product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductTypeCreate = {
  __typename?: 'ProductTypeCreate';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productType?: Maybe<ProductType>;
};

/**
 * Deletes a product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductTypeDelete = {
  __typename?: 'ProductTypeDelete';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productType?: Maybe<ProductType>;
};

export enum ProductTypeEnum {
  Digital = 'DIGITAL',
  Shippable = 'SHIPPABLE'
}

export type ProductTypeFilterInput = {
  configurable?: InputMaybe<ProductTypeConfigurable>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  kind?: InputMaybe<ProductTypeKindEnum>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  productType?: InputMaybe<ProductTypeEnum>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type ProductTypeInput = {
  /** Determines if product of this type has multiple variants. This option mainly simplifies product management in the dashboard. There is always at least one variant created under the hood. */
  hasVariants?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if products are digital. */
  isDigital?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines if shipping is required for products of this variant. */
  isShippingRequired?: InputMaybe<Scalars['Boolean']['input']>;
  /** The product type kind. */
  kind?: InputMaybe<ProductTypeKindEnum>;
  /** Name of the product type. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** List of attributes shared among all product variants. */
  productAttributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Product type slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
  /** ID of a tax class to assign to this product type. All products of this product type would use this tax class, unless it's overridden in the `Product` type. */
  taxClass?: InputMaybe<Scalars['ID']['input']>;
  /**
   * Tax rate for enabled tax gateway.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0.. Use tax classes to control the tax calculation for a product type. If taxCode is provided, Saleor will try to find a tax class with given code (codes are stored in metadata) and assign it. If no tax class is found, it would be created and assigned.
   */
  taxCode?: InputMaybe<Scalars['String']['input']>;
  /** List of attributes used to distinguish between different variants of a product. */
  variantAttributes?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Weight of the ProductType items. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/** An enumeration. */
export enum ProductTypeKindEnum {
  GiftCard = 'GIFT_CARD',
  Normal = 'NORMAL'
}

/**
 * Reorder the attributes of a product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductTypeReorderAttributes = {
  __typename?: 'ProductTypeReorderAttributes';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  /** Product type from which attributes are reordered. */
  productType?: Maybe<ProductType>;
};

export enum ProductTypeSortField {
  /** Sort products by type. */
  Digital = 'DIGITAL',
  /** Sort products by name. */
  Name = 'NAME',
  /** Sort products by shipping. */
  ShippingRequired = 'SHIPPING_REQUIRED'
}

export type ProductTypeSortingInput = {
  /** Specifies the direction in which to sort product types. */
  direction: OrderDirection;
  /** Sort product types by the selected field. */
  field: ProductTypeSortField;
};

/**
 * Updates an existing product type.
 *
 * Requires one of the following permissions: MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES.
 */
export type ProductTypeUpdate = {
  __typename?: 'ProductTypeUpdate';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productType?: Maybe<ProductType>;
};

/**
 * Updates an existing product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductUpdate = {
  __typename?: 'ProductUpdate';
  errors: Array<ProductError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Event sent when product is updated.
 *
 * Added in Saleor 3.2.
 */
export type ProductUpdated = Event & {
  __typename?: 'ProductUpdated';
  /** The category of the product. */
  category?: Maybe<Category>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product the event relates to. */
  product?: Maybe<Product>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product is updated.
 *
 * Added in Saleor 3.2.
 */
export type ProductUpdatedProductArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a version of a product such as different size or color. */
export type ProductVariant = Node & ObjectWithMetadata & {
  __typename?: 'ProductVariant';
  /** List of attributes assigned to this variant. */
  attributes: Array<SelectedAttribute>;
  /** Channel given to retrieve this product variant. Also used by federation gateway to resolve this object in a federated query. */
  channel?: Maybe<Scalars['String']['output']>;
  /**
   * List of price information in channels for the product.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  channelListings?: Maybe<Array<ProductVariantChannelListing>>;
  created: Scalars['DateTime']['output'];
  /**
   * Digital content for the product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContent?: Maybe<DigitalContent>;
  /**
   * External ID of this product.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /**
   * List of images for the product variant.
   * @deprecated This field will be removed in Saleor 4.0. Use the `media` field instead.
   */
  images?: Maybe<Array<ProductImage>>;
  /** Gross margin percentage value. */
  margin?: Maybe<Scalars['Int']['output']>;
  /** List of media for the product variant. */
  media?: Maybe<Array<ProductMedia>>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /**
   * Preorder data for product variant.
   *
   * Added in Saleor 3.1.
   */
  preorder?: Maybe<PreorderData>;
  /** Lists the storefront variant's pricing, the current price and discounts, only meant for displaying. */
  pricing?: Maybe<VariantPricingInfo>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  product: Product;
  /** Quantity of a product available for sale in one checkout. Field value will be `null` when no `limitQuantityPerCheckout` in global settings has been set, and `productVariant` stocks are not tracked. */
  quantityAvailable?: Maybe<Scalars['Int']['output']>;
  quantityLimitPerCustomer?: Maybe<Scalars['Int']['output']>;
  /**
   * Total quantity ordered.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  quantityOrdered?: Maybe<Scalars['Int']['output']>;
  /**
   * Total revenue generated by a variant in given period of time. Note: this field should be queried using `reportProductSales` query as it uses optimizations suitable for such calculations.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  revenue?: Maybe<TaxedMoney>;
  sku?: Maybe<Scalars['String']['output']>;
  /**
   * Stocks for the product variant.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  stocks?: Maybe<Array<Stock>>;
  trackInventory: Scalars['Boolean']['output'];
  /** Returns translated product variant fields for the given language code. */
  translation?: Maybe<ProductVariantTranslation>;
  updatedAt: Scalars['DateTime']['output'];
  weight?: Maybe<Weight>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantAttributesArgs = {
  variantSelection?: InputMaybe<VariantAttributeScope>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantPricingArgs = {
  address?: InputMaybe<AddressInput>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantQuantityAvailableArgs = {
  address?: InputMaybe<AddressInput>;
  countryCode?: InputMaybe<CountryCode>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantRevenueArgs = {
  period?: InputMaybe<ReportingPeriod>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantStocksArgs = {
  address?: InputMaybe<AddressInput>;
  countryCode?: InputMaybe<CountryCode>;
};


/** Represents a version of a product such as different size or color. */
export type ProductVariantTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Event sent when product variant is back in stock.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantBackInStock = Event & {
  __typename?: 'ProductVariantBackInStock';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** Look up a warehouse. */
  warehouse?: Maybe<Warehouse>;
};


/**
 * Event sent when product variant is back in stock.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantBackInStockProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Creates product variants for a given product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantBulkCreate = {
  __typename?: 'ProductVariantBulkCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  bulkProductErrors: Array<BulkProductError>;
  /** Returns how many objects were created. */
  count: Scalars['Int']['output'];
  errors: Array<BulkProductError>;
  /** List of the created variants.This field will be removed in Saleor 4.0. */
  productVariants: Array<ProductVariant>;
  /**
   * List of the created variants.
   *
   * Added in Saleor 3.11.
   */
  results: Array<ProductVariantBulkResult>;
};

export type ProductVariantBulkCreateInput = {
  /** List of attributes specific to this variant. */
  attributes: Array<BulkAttributeValueInput>;
  /** List of prices assigned to channels. */
  channelListings?: InputMaybe<Array<ProductVariantChannelListingAddInput>>;
  /**
   * External ID of this product variant.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product variant metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Variant name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Determines if variant is in preorder.
   *
   * Added in Saleor 3.1.
   */
  preorder?: InputMaybe<PreorderSettingsInput>;
  /**
   * Fields required to update the product variant private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Determines maximum quantity of `ProductVariant`,that can be bought in a single checkout.
   *
   * Added in Saleor 3.1.
   */
  quantityLimitPerCustomer?: InputMaybe<Scalars['Int']['input']>;
  /** Stock keeping unit. */
  sku?: InputMaybe<Scalars['String']['input']>;
  /** Stocks of a product available for sale. */
  stocks?: InputMaybe<Array<StockInput>>;
  /** Determines if the inventory of this variant should be tracked. If false, the quantity won't change when customers buy this item. */
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
  /** Weight of the Product Variant. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/**
 * Deletes product variants.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantBulkDelete = {
  __typename?: 'ProductVariantBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export type ProductVariantBulkError = {
  __typename?: 'ProductVariantBulkError';
  /** List of attributes IDs which causes the error. */
  attributes?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of channel listings IDs which causes the error. */
  channelListings?: Maybe<Array<Scalars['ID']['output']>>;
  /**
   * List of channel IDs which causes the error.
   *
   * Added in Saleor 3.12.
   */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ProductVariantBulkErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /**
   * Path to field that caused the error. A value of `null` indicates that the error isn't associated with a particular field.
   *
   * Added in Saleor 3.14.
   */
  path?: Maybe<Scalars['String']['output']>;
  /**
   * List of stocks IDs which causes the error.
   *
   * Added in Saleor 3.12.
   */
  stocks?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of attribute values IDs which causes the error. */
  values?: Maybe<Array<Scalars['ID']['output']>>;
  /** List of warehouse IDs which causes the error. */
  warehouses?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum ProductVariantBulkErrorCode {
  AttributeAlreadyAssigned = 'ATTRIBUTE_ALREADY_ASSIGNED',
  AttributeCannotBeAssigned = 'ATTRIBUTE_CANNOT_BE_ASSIGNED',
  AttributeVariantsDisabled = 'ATTRIBUTE_VARIANTS_DISABLED',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidPrice = 'INVALID_PRICE',
  NotFound = 'NOT_FOUND',
  NotProductsVariant = 'NOT_PRODUCTS_VARIANT',
  ProductNotAssignedToChannel = 'PRODUCT_NOT_ASSIGNED_TO_CHANNEL',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type ProductVariantBulkResult = {
  __typename?: 'ProductVariantBulkResult';
  /** List of errors occurred on create attempt. */
  errors?: Maybe<Array<ProductVariantBulkError>>;
  /** Product variant data. */
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Update multiple product variants.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantBulkUpdate = {
  __typename?: 'ProductVariantBulkUpdate';
  /** Returns how many objects were updated. */
  count: Scalars['Int']['output'];
  errors: Array<ProductVariantBulkError>;
  /** List of the updated variants. */
  results: Array<ProductVariantBulkResult>;
};

/**
 * Input fields to update product variants.
 *
 * Added in Saleor 3.11.
 */
export type ProductVariantBulkUpdateInput = {
  /** List of attributes specific to this variant. */
  attributes?: InputMaybe<Array<BulkAttributeValueInput>>;
  /**
   * Channel listings input.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  channelListings?: InputMaybe<ProductVariantChannelListingUpdateInput>;
  /**
   * External ID of this product variant.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** ID of the product variant to update. */
  id: Scalars['ID']['input'];
  /**
   * Fields required to update the product variant metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Variant name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Determines if variant is in preorder.
   *
   * Added in Saleor 3.1.
   */
  preorder?: InputMaybe<PreorderSettingsInput>;
  /**
   * Fields required to update the product variant private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Determines maximum quantity of `ProductVariant`,that can be bought in a single checkout.
   *
   * Added in Saleor 3.1.
   */
  quantityLimitPerCustomer?: InputMaybe<Scalars['Int']['input']>;
  /** Stock keeping unit. */
  sku?: InputMaybe<Scalars['String']['input']>;
  /**
   * Stocks input.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  stocks?: InputMaybe<ProductVariantStocksUpdateInput>;
  /** Determines if the inventory of this variant should be tracked. If false, the quantity won't change when customers buy this item. */
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
  /** Weight of the Product Variant. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/** Represents product variant channel listing. */
export type ProductVariantChannelListing = Node & {
  __typename?: 'ProductVariantChannelListing';
  channel: Channel;
  /** Cost price of the variant. */
  costPrice?: Maybe<Money>;
  id: Scalars['ID']['output'];
  /**
   * Gross margin percentage value.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  margin?: Maybe<Scalars['Int']['output']>;
  /**
   * Preorder variant data.
   *
   * Added in Saleor 3.1.
   */
  preorderThreshold?: Maybe<PreorderThreshold>;
  price?: Maybe<Money>;
};

export type ProductVariantChannelListingAddInput = {
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Cost price of the variant in channel. */
  costPrice?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /**
   * The threshold for preorder variant in channel.
   *
   * Added in Saleor 3.1.
   */
  preorderThreshold?: InputMaybe<Scalars['Int']['input']>;
  /** Price of the particular variant in channel. */
  price: Scalars['PositiveDecimal']['input'];
};

/**
 * Manage product variant prices in channels.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantChannelListingUpdate = {
  __typename?: 'ProductVariantChannelListingUpdate';
  errors: Array<ProductChannelListingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productChannelListingErrors: Array<ProductChannelListingError>;
  /** An updated product variant instance. */
  variant?: Maybe<ProductVariant>;
};

export type ProductVariantChannelListingUpdateInput = {
  /** List of channels to create variant channel listings. */
  create?: InputMaybe<Array<ProductVariantChannelListingAddInput>>;
  /** List of channel listings to remove. */
  remove?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of channel listings to update. */
  update?: InputMaybe<Array<ChannelListingUpdateInput>>;
};

export type ProductVariantCountableConnection = {
  __typename?: 'ProductVariantCountableConnection';
  edges: Array<ProductVariantCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type ProductVariantCountableEdge = {
  __typename?: 'ProductVariantCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: ProductVariant;
};

/**
 * Creates a new variant for a product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantCreate = {
  __typename?: 'ProductVariantCreate';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productVariant?: Maybe<ProductVariant>;
};

export type ProductVariantCreateInput = {
  /** List of attributes specific to this variant. */
  attributes: Array<AttributeValueInput>;
  /**
   * External ID of this product variant.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product variant metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Variant name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Determines if variant is in preorder.
   *
   * Added in Saleor 3.1.
   */
  preorder?: InputMaybe<PreorderSettingsInput>;
  /**
   * Fields required to update the product variant private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** Product ID of which type is the variant. */
  product: Scalars['ID']['input'];
  /**
   * Determines maximum quantity of `ProductVariant`,that can be bought in a single checkout.
   *
   * Added in Saleor 3.1.
   */
  quantityLimitPerCustomer?: InputMaybe<Scalars['Int']['input']>;
  /** Stock keeping unit. */
  sku?: InputMaybe<Scalars['String']['input']>;
  /** Stocks of a product available for sale. */
  stocks?: InputMaybe<Array<StockInput>>;
  /** Determines if the inventory of this variant should be tracked. If false, the quantity won't change when customers buy this item. */
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
  /** Weight of the Product Variant. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/**
 * Event sent when new product variant is created.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantCreated = Event & {
  __typename?: 'ProductVariantCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new product variant is created.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantCreatedProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantDelete = {
  __typename?: 'ProductVariantDelete';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Event sent when product variant is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantDeleted = Event & {
  __typename?: 'ProductVariantDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product variant is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantDeletedProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type ProductVariantFilterInput = {
  isPreorder?: InputMaybe<Scalars['Boolean']['input']>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  sku?: InputMaybe<Array<Scalars['String']['input']>>;
  updatedAt?: InputMaybe<DateTimeRangeInput>;
};

export type ProductVariantInput = {
  /** List of attributes specific to this variant. */
  attributes?: InputMaybe<Array<AttributeValueInput>>;
  /**
   * External ID of this product variant.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the product variant metadata.
   *
   * Added in Saleor 3.8.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Variant name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Determines if variant is in preorder.
   *
   * Added in Saleor 3.1.
   */
  preorder?: InputMaybe<PreorderSettingsInput>;
  /**
   * Fields required to update the product variant private metadata.
   *
   * Added in Saleor 3.8.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Determines maximum quantity of `ProductVariant`,that can be bought in a single checkout.
   *
   * Added in Saleor 3.1.
   */
  quantityLimitPerCustomer?: InputMaybe<Scalars['Int']['input']>;
  /** Stock keeping unit. */
  sku?: InputMaybe<Scalars['String']['input']>;
  /** Determines if the inventory of this variant should be tracked. If false, the quantity won't change when customers buy this item. */
  trackInventory?: InputMaybe<Scalars['Boolean']['input']>;
  /** Weight of the Product Variant. */
  weight?: InputMaybe<Scalars['WeightScalar']['input']>;
};

/**
 * Event sent when product variant metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ProductVariantMetadataUpdated = Event & {
  __typename?: 'ProductVariantMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product variant metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ProductVariantMetadataUpdatedProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when product variant is out of stock.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantOutOfStock = Event & {
  __typename?: 'ProductVariantOutOfStock';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** Look up a warehouse. */
  warehouse?: Maybe<Warehouse>;
};


/**
 * Event sent when product variant is out of stock.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantOutOfStockProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deactivates product variant preorder. It changes all preorder allocation into regular allocation.
 *
 * Added in Saleor 3.1.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantPreorderDeactivate = {
  __typename?: 'ProductVariantPreorderDeactivate';
  errors: Array<ProductError>;
  /** Product variant with ended preorder. */
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Reorder the variants of a product. Mutation updates updated_at on product and triggers PRODUCT_UPDATED webhook.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantReorder = {
  __typename?: 'ProductVariantReorder';
  errors: Array<ProductError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

/**
 * Reorder product variant attribute values.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantReorderAttributeValues = {
  __typename?: 'ProductVariantReorderAttributeValues';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  /** Product variant from which attribute values are reordered. */
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Set default variant for a product. Mutation triggers PRODUCT_UPDATED webhook.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantSetDefault = {
  __typename?: 'ProductVariantSetDefault';
  errors: Array<ProductError>;
  product?: Maybe<Product>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
};

export enum ProductVariantSortField {
  /** Sort products variants by last modified at. */
  LastModifiedAt = 'LAST_MODIFIED_AT'
}

export type ProductVariantSortingInput = {
  /** Specifies the direction in which to sort productVariants. */
  direction: OrderDirection;
  /** Sort productVariants by the selected field. */
  field: ProductVariantSortField;
};

/**
 * Event sent when product variant stock is updated.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type ProductVariantStockUpdated = Event & {
  __typename?: 'ProductVariantStockUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** Look up a warehouse. */
  warehouse?: Maybe<Warehouse>;
};


/**
 * Event sent when product variant stock is updated.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type ProductVariantStockUpdatedProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Creates stocks for product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantStocksCreate = {
  __typename?: 'ProductVariantStocksCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  bulkStockErrors: Array<BulkStockError>;
  errors: Array<BulkStockError>;
  /** Updated product variant. */
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Delete stocks from product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantStocksDelete = {
  __typename?: 'ProductVariantStocksDelete';
  errors: Array<StockError>;
  /** Updated product variant. */
  productVariant?: Maybe<ProductVariant>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  stockErrors: Array<StockError>;
};

/**
 * Update stocks for product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantStocksUpdate = {
  __typename?: 'ProductVariantStocksUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  bulkStockErrors: Array<BulkStockError>;
  errors: Array<BulkStockError>;
  /** Updated product variant. */
  productVariant?: Maybe<ProductVariant>;
};

export type ProductVariantStocksUpdateInput = {
  /** List of warehouses to create stocks. */
  create?: InputMaybe<Array<StockInput>>;
  /** List of stocks to remove. */
  remove?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of stocks to update. */
  update?: InputMaybe<Array<StockUpdateInput>>;
};

export type ProductVariantTranslatableContent = Node & {
  __typename?: 'ProductVariantTranslatableContent';
  /** List of product variant attribute values that can be translated. */
  attributeValues: Array<AttributeValueTranslatableContent>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /**
   * Represents a version of a product such as different size or color.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  productVariant?: Maybe<ProductVariant>;
  /** Returns translated product variant fields for the given language code. */
  translation?: Maybe<ProductVariantTranslation>;
};


export type ProductVariantTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a product variant.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type ProductVariantTranslate = {
  __typename?: 'ProductVariantTranslate';
  errors: Array<TranslationError>;
  productVariant?: Maybe<ProductVariant>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type ProductVariantTranslation = Node & {
  __typename?: 'ProductVariantTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name: Scalars['String']['output'];
};

/**
 * Updates an existing variant for product.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type ProductVariantUpdate = {
  __typename?: 'ProductVariantUpdate';
  errors: Array<ProductError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Event sent when product variant is updated.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantUpdated = Event & {
  __typename?: 'ProductVariantUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The product variant the event relates to. */
  productVariant?: Maybe<ProductVariant>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when product variant is updated.
 *
 * Added in Saleor 3.2.
 */
export type ProductVariantUpdatedProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type PublishableChannelListingInput = {
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Determines if object is visible to customers. */
  isPublished?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Publication date. ISO 8601 standard.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `publishedAt` field instead.
   */
  publicationDate?: InputMaybe<Scalars['Date']['input']>;
  /**
   * Publication date time. ISO 8601 standard.
   *
   * Added in Saleor 3.3.
   */
  publishedAt?: InputMaybe<Scalars['DateTime']['input']>;
};

export type Query = {
  __typename?: 'Query';
  _entities?: Maybe<Array<Maybe<_Entity>>>;
  _service?: Maybe<_Service>;
  /**
   * Look up an address by ID.
   *
   * Requires one of the following permissions: MANAGE_USERS, OWNER.
   */
  address?: Maybe<Address>;
  /** Returns address validation rules. */
  addressValidationRules?: Maybe<AddressValidationData>;
  /**
   * Look up an app by ID. If ID is not provided, return the currently authenticated app.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER AUTHENTICATED_APP. The authenticated app has access to its resources. Fetching different apps requires MANAGE_APPS permission.
   */
  app?: Maybe<App>;
  /**
   * Look up an app extension by ID.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  appExtension?: Maybe<AppExtension>;
  /**
   * List of all extensions.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  appExtensions?: Maybe<AppExtensionCountableConnection>;
  /**
   * List of the apps.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, MANAGE_APPS.
   */
  apps?: Maybe<AppCountableConnection>;
  /**
   * List of all apps installations
   *
   * Requires one of the following permissions: MANAGE_APPS.
   */
  appsInstallations: Array<AppInstallation>;
  /** Look up an attribute by ID, slug or external reference. */
  attribute?: Maybe<Attribute>;
  /** List of the shop's attributes. */
  attributes?: Maybe<AttributeCountableConnection>;
  /** List of the shop's categories. */
  categories?: Maybe<CategoryCountableConnection>;
  /** Look up a category by ID or slug. */
  category?: Maybe<Category>;
  /** Look up a channel by ID or slug. */
  channel?: Maybe<Channel>;
  /**
   * List of all channels.
   *
   * Requires one of the following permissions: AUTHENTICATED_APP, AUTHENTICATED_STAFF_USER.
   */
  channels?: Maybe<Array<Channel>>;
  /** Look up a checkout by token and slug of channel. */
  checkout?: Maybe<Checkout>;
  /**
   * List of checkout lines.
   *
   * Requires one of the following permissions: MANAGE_CHECKOUTS.
   */
  checkoutLines?: Maybe<CheckoutLineCountableConnection>;
  /**
   * List of checkouts.
   *
   * Requires one of the following permissions: MANAGE_CHECKOUTS.
   */
  checkouts?: Maybe<CheckoutCountableConnection>;
  /** Look up a collection by ID. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  collection?: Maybe<Collection>;
  /** List of the shop's collections. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  collections?: Maybe<CollectionCountableConnection>;
  /**
   * List of the shop's customers.
   *
   * Requires one of the following permissions: MANAGE_ORDERS, MANAGE_USERS.
   */
  customers?: Maybe<UserCountableConnection>;
  /**
   * Look up digital content by ID.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContent?: Maybe<DigitalContent>;
  /**
   * List of digital content.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  digitalContents?: Maybe<DigitalContentCountableConnection>;
  /**
   * List of draft orders.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  draftOrders?: Maybe<OrderCountableConnection>;
  /**
   * Look up a export file by ID.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  exportFile?: Maybe<ExportFile>;
  /**
   * List of export files.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  exportFiles?: Maybe<ExportFileCountableConnection>;
  /**
   * Look up a gift card by ID.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCard?: Maybe<GiftCard>;
  /**
   * List of gift card currencies.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardCurrencies: Array<Scalars['String']['output']>;
  /**
   * Gift card related settings from site settings.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardSettings: GiftCardSettings;
  /**
   * List of gift card tags.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCardTags?: Maybe<GiftCardTagCountableConnection>;
  /**
   * List of gift cards.
   *
   * Requires one of the following permissions: MANAGE_GIFT_CARD.
   */
  giftCards?: Maybe<GiftCardCountableConnection>;
  /**
   * List of activity events to display on homepage (at the moment it only contains order-events).
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  homepageEvents?: Maybe<OrderEventCountableConnection>;
  /** Return the currently authenticated user. */
  me?: Maybe<User>;
  /** Look up a navigation menu by ID or name. */
  menu?: Maybe<Menu>;
  /** Look up a menu item by ID. */
  menuItem?: Maybe<MenuItem>;
  /** List of the storefronts's menu items. */
  menuItems?: Maybe<MenuItemCountableConnection>;
  /** List of the storefront's menus. */
  menus?: Maybe<MenuCountableConnection>;
  /** Look up an order by ID or external reference. */
  order?: Maybe<Order>;
  /**
   * Look up an order by token.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  orderByToken?: Maybe<Order>;
  /**
   * Order related settings from site settings. Returns `orderSettings` for the first `channel` in alphabetical order.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   * @deprecated This field will be removed in Saleor 4.0. Use the `channel` query to fetch the `orderSettings` field instead.
   */
  orderSettings?: Maybe<OrderSettings>;
  /**
   * List of orders.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  orders?: Maybe<OrderCountableConnection>;
  /**
   * Return the total sales amount from a specific period.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  ordersTotal?: Maybe<TaxedMoney>;
  /** Look up a page by ID or slug. */
  page?: Maybe<Page>;
  /** Look up a page type by ID. */
  pageType?: Maybe<PageType>;
  /** List of the page types. */
  pageTypes?: Maybe<PageTypeCountableConnection>;
  /** List of the shop's pages. */
  pages?: Maybe<PageCountableConnection>;
  /**
   * Look up a payment by ID.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  payment?: Maybe<Payment>;
  /**
   * List of payments.
   *
   * Requires one of the following permissions: MANAGE_ORDERS.
   */
  payments?: Maybe<PaymentCountableConnection>;
  /**
   * Look up permission group by ID.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  permissionGroup?: Maybe<Group>;
  /**
   * List of permission groups.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  permissionGroups?: Maybe<GroupCountableConnection>;
  /**
   * Look up a plugin by ID.
   *
   * Requires one of the following permissions: MANAGE_PLUGINS.
   */
  plugin?: Maybe<Plugin>;
  /**
   * List of plugins.
   *
   * Requires one of the following permissions: MANAGE_PLUGINS.
   */
  plugins?: Maybe<PluginCountableConnection>;
  /** Look up a product by ID. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  product?: Maybe<Product>;
  /** Look up a product type by ID. */
  productType?: Maybe<ProductType>;
  /** List of the shop's product types. */
  productTypes?: Maybe<ProductTypeCountableConnection>;
  /** Look up a product variant by ID or SKU. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  productVariant?: Maybe<ProductVariant>;
  /** List of product variants. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  productVariants?: Maybe<ProductVariantCountableConnection>;
  /** List of the shop's products. Requires one of the following permissions to include the unpublished items: MANAGE_ORDERS, MANAGE_DISCOUNTS, MANAGE_PRODUCTS. */
  products?: Maybe<ProductCountableConnection>;
  /**
   * List of top selling products.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  reportProductSales?: Maybe<ProductVariantCountableConnection>;
  /**
   * Look up a sale by ID.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  sale?: Maybe<Sale>;
  /**
   * List of the shop's sales.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  sales?: Maybe<SaleCountableConnection>;
  /**
   * Look up a shipping zone by ID.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZone?: Maybe<ShippingZone>;
  /**
   * List of the shop's shipping zones.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  shippingZones?: Maybe<ShippingZoneCountableConnection>;
  /** Return information about the shop. */
  shop: Shop;
  /**
   * List of the shop's staff users.
   *
   * Requires one of the following permissions: MANAGE_STAFF.
   */
  staffUsers?: Maybe<UserCountableConnection>;
  /**
   * Look up a stock by ID
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  stock?: Maybe<Stock>;
  /**
   * List of stocks.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS.
   */
  stocks?: Maybe<StockCountableConnection>;
  /**
   * Look up a tax class.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClass?: Maybe<TaxClass>;
  /**
   * List of tax classes.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClasses?: Maybe<TaxClassCountableConnection>;
  /**
   * Look up a tax configuration.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxConfiguration?: Maybe<TaxConfiguration>;
  /**
   * List of tax configurations.
   *
   * Added in Saleor 3.9.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxConfigurations?: Maybe<TaxConfigurationCountableConnection>;
  /**
   * Tax class rates grouped by country.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxCountryConfiguration?: Maybe<TaxCountryConfiguration>;
  /**
   *
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxCountryConfigurations?: Maybe<Array<TaxCountryConfiguration>>;
  /** List of all tax rates available from tax gateway. */
  taxTypes?: Maybe<Array<TaxType>>;
  /**
   * Look up a transaction by ID.
   *
   * Added in Saleor 3.6.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   *
   * Requires one of the following permissions: HANDLE_PAYMENTS.
   */
  transaction?: Maybe<TransactionItem>;
  /**
   * Lookup a translatable item by ID.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  translation?: Maybe<TranslatableItem>;
  /**
   * Returns a list of all translatable items of a given kind.
   *
   * Requires one of the following permissions: MANAGE_TRANSLATIONS.
   */
  translations?: Maybe<TranslatableItemConnection>;
  /**
   * Look up a user by ID or email address.
   *
   * Requires one of the following permissions: MANAGE_STAFF, MANAGE_USERS, MANAGE_ORDERS.
   */
  user?: Maybe<User>;
  /**
   * Look up a voucher by ID.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  voucher?: Maybe<Voucher>;
  /**
   * List of the shop's vouchers.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  vouchers?: Maybe<VoucherCountableConnection>;
  /**
   * Look up a warehouse by ID.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS, MANAGE_SHIPPING.
   */
  warehouse?: Maybe<Warehouse>;
  /**
   * List of warehouses.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS, MANAGE_SHIPPING.
   */
  warehouses?: Maybe<WarehouseCountableConnection>;
  /** Look up a webhook by ID. Requires one of the following permissions: MANAGE_APPS, OWNER. */
  webhook?: Maybe<Webhook>;
  /**
   * List of all available webhook events.
   *
   * Requires one of the following permissions: MANAGE_APPS.
   * @deprecated This field will be removed in Saleor 4.0. Use `WebhookEventTypeAsyncEnum` and `WebhookEventTypeSyncEnum` to get available event types.
   */
  webhookEvents?: Maybe<Array<WebhookEvent>>;
  /** Retrieve a sample payload for a given webhook event based on real data. It can be useful for some integrations where sample payload is required. */
  webhookSamplePayload?: Maybe<Scalars['JSONString']['output']>;
};


export type Query_EntitiesArgs = {
  representations?: InputMaybe<Array<InputMaybe<Scalars['_Any']['input']>>>;
};


export type QueryAddressArgs = {
  id: Scalars['ID']['input'];
};


export type QueryAddressValidationRulesArgs = {
  city?: InputMaybe<Scalars['String']['input']>;
  cityArea?: InputMaybe<Scalars['String']['input']>;
  countryArea?: InputMaybe<Scalars['String']['input']>;
  countryCode: CountryCode;
};


export type QueryAppArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryAppExtensionArgs = {
  id: Scalars['ID']['input'];
};


export type QueryAppExtensionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AppExtensionFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryAppsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AppFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<AppSortingInput>;
};


export type QueryAttributeArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryAttributesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<AttributeFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<AttributeSortingInput>;
  where?: InputMaybe<AttributeWhereInput>;
};


export type QueryCategoriesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<CategoryFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  level?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<CategorySortingInput>;
};


export type QueryCategoryArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryChannelArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryCheckoutArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  token?: InputMaybe<Scalars['UUID']['input']>;
};


export type QueryCheckoutLinesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryCheckoutsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<CheckoutFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<CheckoutSortingInput>;
};


export type QueryCollectionArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryCollectionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<CollectionFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<CollectionSortingInput>;
};


export type QueryCustomersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<CustomerFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<UserSortingInput>;
};


export type QueryDigitalContentArgs = {
  id: Scalars['ID']['input'];
};


export type QueryDigitalContentsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryDraftOrdersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<OrderDraftFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<OrderSortingInput>;
};


export type QueryExportFileArgs = {
  id: Scalars['ID']['input'];
};


export type QueryExportFilesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ExportFileFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ExportFileSortingInput>;
};


export type QueryGiftCardArgs = {
  id: Scalars['ID']['input'];
};


export type QueryGiftCardTagsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<GiftCardTagFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryGiftCardsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<GiftCardFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<GiftCardSortingInput>;
};


export type QueryHomepageEventsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryMenuArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryMenuItemArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
};


export type QueryMenuItemsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<MenuItemFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<MenuItemSortingInput>;
};


export type QueryMenusArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<MenuFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<MenuSortingInput>;
};


export type QueryOrderArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryOrderByTokenArgs = {
  token: Scalars['UUID']['input'];
};


export type QueryOrdersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<OrderFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<OrderSortingInput>;
};


export type QueryOrdersTotalArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  period?: InputMaybe<ReportingPeriod>;
};


export type QueryPageArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryPageTypeArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPageTypesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<PageTypeFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<PageTypeSortingInput>;
};


export type QueryPagesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<PageFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<PageSortingInput>;
};


export type QueryPaymentArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPaymentsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<PaymentFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryPermissionGroupArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPermissionGroupsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<PermissionGroupFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<PermissionGroupSortingInput>;
};


export type QueryPluginArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPluginsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<PluginFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<PluginSortingInput>;
};


export type QueryProductArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


export type QueryProductTypeArgs = {
  id: Scalars['ID']['input'];
};


export type QueryProductTypesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ProductTypeFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ProductTypeSortingInput>;
};


export type QueryProductVariantArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
  sku?: InputMaybe<Scalars['String']['input']>;
};


export type QueryProductVariantsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ProductVariantFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ProductVariantSortingInput>;
};


export type QueryProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ProductFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<ProductOrder>;
};


export type QueryReportProductSalesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel: Scalars['String']['input'];
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  period: ReportingPeriod;
};


export type QuerySaleArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
};


export type QuerySalesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<SaleFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  query?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<SaleSortingInput>;
};


export type QueryShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
};


export type QueryShippingZonesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<ShippingZoneFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryStaffUsersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<StaffUserInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<UserSortingInput>;
};


export type QueryStockArgs = {
  id: Scalars['ID']['input'];
};


export type QueryStocksArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<StockFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryTaxClassArgs = {
  id: Scalars['ID']['input'];
};


export type QueryTaxClassesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<TaxClassFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<TaxClassSortingInput>;
};


export type QueryTaxConfigurationArgs = {
  id: Scalars['ID']['input'];
};


export type QueryTaxConfigurationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<TaxConfigurationFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryTaxCountryConfigurationArgs = {
  countryCode: CountryCode;
};


export type QueryTransactionArgs = {
  id: Scalars['ID']['input'];
};


export type QueryTranslationArgs = {
  id: Scalars['ID']['input'];
  kind: TranslatableKinds;
};


export type QueryTranslationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  kind: TranslatableKinds;
  last?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryUserArgs = {
  email?: InputMaybe<Scalars['String']['input']>;
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryVoucherArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
};


export type QueryVouchersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<VoucherFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  query?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<VoucherSortingInput>;
};


export type QueryWarehouseArgs = {
  externalReference?: InputMaybe<Scalars['String']['input']>;
  id?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryWarehousesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<WarehouseFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<WarehouseSortingInput>;
};


export type QueryWebhookArgs = {
  id: Scalars['ID']['input'];
};


export type QueryWebhookSamplePayloadArgs = {
  eventType: WebhookSampleEventTypeEnum;
};

/** Represents a reduced VAT rate for a particular type of goods. */
export type ReducedRate = {
  __typename?: 'ReducedRate';
  /** Reduced VAT rate in percent. */
  rate: Scalars['Float']['output'];
  /** A type of goods. */
  rateType: Scalars['String']['output'];
};

/** Refresh JWT token. Mutation tries to take refreshToken from the input. If it fails it will try to take `refreshToken` from the http-only cookie `refreshToken`. `csrfToken` is required when `refreshToken` is provided as a cookie. */
export type RefreshToken = {
  __typename?: 'RefreshToken';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** JWT token, required to authenticate. */
  token?: Maybe<Scalars['String']['output']>;
  /** A user instance. */
  user?: Maybe<User>;
};

export type ReorderInput = {
  /** The ID of the item to move. */
  id: Scalars['ID']['input'];
  /** The new relative sorting position of the item (from -inf to +inf). 1 moves the item one position forward, -1 moves the item one position backward, 0 leaves the item unchanged. */
  sortOrder?: InputMaybe<Scalars['Int']['input']>;
};

export enum ReportingPeriod {
  ThisMonth = 'THIS_MONTH',
  Today = 'TODAY'
}

/**
 * Request email change of the logged in user.
 *
 * Requires one of the following permissions: AUTHENTICATED_USER.
 */
export type RequestEmailChange = {
  __typename?: 'RequestEmailChange';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** A user instance. */
  user?: Maybe<User>;
};

/** Sends an email with the account password modification link. */
export type RequestPasswordReset = {
  __typename?: 'RequestPasswordReset';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
};

/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type Sale = Node & ObjectWithMetadata & {
  __typename?: 'Sale';
  /** List of categories this sale applies to. */
  categories?: Maybe<CategoryCountableConnection>;
  /**
   * List of channels available for the sale.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  channelListings?: Maybe<Array<SaleChannelListing>>;
  /**
   * List of collections this sale applies to.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  collections?: Maybe<CollectionCountableConnection>;
  created: Scalars['DateTime']['output'];
  /** Currency code for sale. */
  currency?: Maybe<Scalars['String']['output']>;
  /** Sale value. */
  discountValue?: Maybe<Scalars['Float']['output']>;
  endDate?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * List of products this sale applies to.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  products?: Maybe<ProductCountableConnection>;
  startDate: Scalars['DateTime']['output'];
  /** Returns translated sale fields for the given language code. */
  translation?: Maybe<SaleTranslation>;
  type: SaleType;
  updatedAt: Scalars['DateTime']['output'];
  /**
   * List of product variants this sale applies to.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  variants?: Maybe<ProductVariantCountableConnection>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleCategoriesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleCollectionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SalePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SalePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleTranslationArgs = {
  languageCode: LanguageCodeEnum;
};


/** Sales allow creating discounts for categories, collections or products and are visible to all the customers. */
export type SaleVariantsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};

/**
 * Adds products, categories, collections to a voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleAddCatalogues = {
  __typename?: 'SaleAddCatalogues';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** Sale of which catalogue IDs will be modified. */
  sale?: Maybe<Sale>;
};

/**
 * Deletes sales.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleBulkDelete = {
  __typename?: 'SaleBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
};

/** Represents sale channel listing. */
export type SaleChannelListing = Node & {
  __typename?: 'SaleChannelListing';
  channel: Channel;
  currency: Scalars['String']['output'];
  discountValue: Scalars['Float']['output'];
  id: Scalars['ID']['output'];
};

export type SaleChannelListingAddInput = {
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** The value of the discount. */
  discountValue: Scalars['PositiveDecimal']['input'];
};

export type SaleChannelListingInput = {
  /** List of channels to which the sale should be assigned. */
  addChannels?: InputMaybe<Array<SaleChannelListingAddInput>>;
  /** List of channels from which the sale should be unassigned. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Manage sale's availability in channels.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleChannelListingUpdate = {
  __typename?: 'SaleChannelListingUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** An updated sale instance. */
  sale?: Maybe<Sale>;
};

export type SaleCountableConnection = {
  __typename?: 'SaleCountableConnection';
  edges: Array<SaleCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type SaleCountableEdge = {
  __typename?: 'SaleCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Sale;
};

/**
 * Creates a new sale.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleCreate = {
  __typename?: 'SaleCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  sale?: Maybe<Sale>;
};

/**
 * Event sent when new sale is created.
 *
 * Added in Saleor 3.2.
 */
export type SaleCreated = Event & {
  __typename?: 'SaleCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The sale the event relates to. */
  sale?: Maybe<Sale>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new sale is created.
 *
 * Added in Saleor 3.2.
 */
export type SaleCreatedSaleArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a sale.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleDelete = {
  __typename?: 'SaleDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  sale?: Maybe<Sale>;
};

/**
 * Event sent when sale is deleted.
 *
 * Added in Saleor 3.2.
 */
export type SaleDeleted = Event & {
  __typename?: 'SaleDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The sale the event relates to. */
  sale?: Maybe<Sale>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when sale is deleted.
 *
 * Added in Saleor 3.2.
 */
export type SaleDeletedSaleArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type SaleFilterInput = {
  metadata?: InputMaybe<Array<MetadataFilter>>;
  saleType?: InputMaybe<DiscountValueTypeEnum>;
  search?: InputMaybe<Scalars['String']['input']>;
  started?: InputMaybe<DateTimeRangeInput>;
  status?: InputMaybe<Array<DiscountStatusEnum>>;
  updatedAt?: InputMaybe<DateTimeRangeInput>;
};

export type SaleInput = {
  /** Categories related to the discount. */
  categories?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Collections related to the discount. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** End date of the voucher in ISO 8601 format. */
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** Voucher name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Products related to the discount. */
  products?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Start date of the voucher in ISO 8601 format. */
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** Fixed or percentage. */
  type?: InputMaybe<DiscountValueTypeEnum>;
  /** Value of the voucher. */
  value?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  variants?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Removes products, categories, collections from a sale.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleRemoveCatalogues = {
  __typename?: 'SaleRemoveCatalogues';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** Sale of which catalogue IDs will be modified. */
  sale?: Maybe<Sale>;
};

export enum SaleSortField {
  /** Sort sales by created at. */
  CreatedAt = 'CREATED_AT',
  /** Sort sales by end date. */
  EndDate = 'END_DATE',
  /** Sort sales by last modified at. */
  LastModifiedAt = 'LAST_MODIFIED_AT',
  /** Sort sales by name. */
  Name = 'NAME',
  /** Sort sales by start date. */
  StartDate = 'START_DATE',
  /** Sort sales by type. */
  Type = 'TYPE',
  /**
   * Sort sales by value.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Value = 'VALUE'
}

export type SaleSortingInput = {
  /**
   * Specifies the channel in which to sort the data.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Specifies the direction in which to sort sales. */
  direction: OrderDirection;
  /** Sort sales by the selected field. */
  field: SaleSortField;
};

/**
 * The event informs about the start or end of the sale.
 *
 * Added in Saleor 3.5.
 */
export type SaleToggle = Event & {
  __typename?: 'SaleToggle';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /**
   * The sale the event relates to.
   *
   * Added in Saleor 3.5.
   */
  sale?: Maybe<Sale>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * The event informs about the start or end of the sale.
 *
 * Added in Saleor 3.5.
 */
export type SaleToggleSaleArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type SaleTranslatableContent = Node & {
  __typename?: 'SaleTranslatableContent';
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /**
   * Sales allow creating discounts for categories, collections or products and are visible to all the customers.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  sale?: Maybe<Sale>;
  /** Returns translated sale fields for the given language code. */
  translation?: Maybe<SaleTranslation>;
};


export type SaleTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a sale.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type SaleTranslate = {
  __typename?: 'SaleTranslate';
  errors: Array<TranslationError>;
  sale?: Maybe<Sale>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type SaleTranslation = Node & {
  __typename?: 'SaleTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
};

export enum SaleType {
  Fixed = 'FIXED',
  Percentage = 'PERCENTAGE'
}

/**
 * Updates a sale.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type SaleUpdate = {
  __typename?: 'SaleUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  sale?: Maybe<Sale>;
};

/**
 * Event sent when sale is updated.
 *
 * Added in Saleor 3.2.
 */
export type SaleUpdated = Event & {
  __typename?: 'SaleUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The sale the event relates to. */
  sale?: Maybe<Sale>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when sale is updated.
 *
 * Added in Saleor 3.2.
 */
export type SaleUpdatedSaleArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a custom attribute. */
export type SelectedAttribute = {
  __typename?: 'SelectedAttribute';
  /** Name of an attribute displayed in the interface. */
  attribute: Attribute;
  /** Values of an attribute. */
  values: Array<AttributeValue>;
};

export type SeoInput = {
  /** SEO description. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** SEO title. */
  title?: InputMaybe<Scalars['String']['input']>;
};

/** Sets the user's password from the token sent by email using the RequestPasswordReset mutation. */
export type SetPassword = {
  __typename?: 'SetPassword';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** CSRF token required to re-generate access token. */
  csrfToken?: Maybe<Scalars['String']['output']>;
  errors: Array<AccountError>;
  /** JWT refresh token, required to re-generate access token. */
  refreshToken?: Maybe<Scalars['String']['output']>;
  /** JWT token, required to authenticate. */
  token?: Maybe<Scalars['String']['output']>;
  /** A user instance. */
  user?: Maybe<User>;
};

export type ShippingError = {
  __typename?: 'ShippingError';
  /** List of channels IDs which causes the error. */
  channels?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error code. */
  code: ShippingErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of warehouse IDs which causes the error. */
  warehouses?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum ShippingErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  MaxLessThanMin = 'MAX_LESS_THAN_MIN',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

/**
 * List shipping methods for checkout.
 *
 * Added in Saleor 3.6.
 */
export type ShippingListMethodsForCheckout = Event & {
  __typename?: 'ShippingListMethodsForCheckout';
  /** The checkout the event relates to. */
  checkout?: Maybe<Checkout>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /**
   * Shipping methods that can be used with this checkout.
   *
   * Added in Saleor 3.6.
   */
  shippingMethods?: Maybe<Array<ShippingMethod>>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethod = Node & ObjectWithMetadata & {
  __typename?: 'ShippingMethod';
  /** Describes if this shipping method is active and can be selected. */
  active: Scalars['Boolean']['output'];
  /**
   * Shipping method description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /** Unique ID of ShippingMethod available for Order. */
  id: Scalars['ID']['output'];
  /** Maximum delivery days for this shipping method. */
  maximumDeliveryDays?: Maybe<Scalars['Int']['output']>;
  /** Maximum order price for this shipping method. */
  maximumOrderPrice?: Maybe<Money>;
  /**
   * Maximum order weight for this shipping method.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  maximumOrderWeight?: Maybe<Weight>;
  /** Message connected to this shipping method. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /** Public metadata. Use `keys` to control which fields you want to include. The default is to include everything. */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Minimum delivery days for this shipping method. */
  minimumDeliveryDays?: Maybe<Scalars['Int']['output']>;
  /** Minimal order price for this shipping method. */
  minimumOrderPrice?: Maybe<Money>;
  /**
   * Minimum order weight for this shipping method.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  minimumOrderWeight?: Maybe<Weight>;
  /** Shipping method name. */
  name: Scalars['String']['output'];
  /** The price of selected shipping method. */
  price: Money;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /** Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything. */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** Returns translated shipping method fields for the given language code. */
  translation?: Maybe<ShippingMethodTranslation>;
  /**
   * Type of the shipping method.
   * @deprecated This field will be removed in Saleor 4.0.
   */
  type?: Maybe<ShippingMethodTypeEnum>;
};


/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethodMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethodMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethodPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethodPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Shipping methods that can be used as means of shipping for orders and checkouts. */
export type ShippingMethodTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/** Represents shipping method channel listing. */
export type ShippingMethodChannelListing = Node & {
  __typename?: 'ShippingMethodChannelListing';
  channel: Channel;
  id: Scalars['ID']['output'];
  maximumOrderPrice?: Maybe<Money>;
  minimumOrderPrice?: Maybe<Money>;
  price?: Maybe<Money>;
};

export type ShippingMethodChannelListingAddInput = {
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Maximum order price to use this shipping method. */
  maximumOrderPrice?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** Minimum order price to use this shipping method. */
  minimumOrderPrice?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** Shipping price of the shipping method in this channel. */
  price?: InputMaybe<Scalars['PositiveDecimal']['input']>;
};

export type ShippingMethodChannelListingInput = {
  /** List of channels to which the shipping method should be assigned. */
  addChannels?: InputMaybe<Array<ShippingMethodChannelListingAddInput>>;
  /** List of channels from which the shipping method should be unassigned. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Manage shipping method's availability in channels.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingMethodChannelListingUpdate = {
  __typename?: 'ShippingMethodChannelListingUpdate';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  /** An updated shipping method instance. */
  shippingMethod?: Maybe<ShippingMethodType>;
};

/** Represents shipping method postal code rule. */
export type ShippingMethodPostalCodeRule = Node & {
  __typename?: 'ShippingMethodPostalCodeRule';
  /** End address range. */
  end?: Maybe<Scalars['String']['output']>;
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /** Inclusion type of the postal code rule. */
  inclusionType?: Maybe<PostalCodeRuleInclusionTypeEnum>;
  /** Start address range. */
  start?: Maybe<Scalars['String']['output']>;
};

export type ShippingMethodTranslatableContent = Node & {
  __typename?: 'ShippingMethodTranslatableContent';
  /**
   * Description of the shipping method.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  /**
   * Shipping method are the methods you'll use to get customer's orders  to them. They are directly exposed to the customers.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  shippingMethod?: Maybe<ShippingMethodType>;
  /** Returns translated shipping method fields for the given language code. */
  translation?: Maybe<ShippingMethodTranslation>;
};


export type ShippingMethodTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

export type ShippingMethodTranslation = Node & {
  __typename?: 'ShippingMethodTranslation';
  /**
   * Translated description of the shipping method.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
};

/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodType = Node & ObjectWithMetadata & {
  __typename?: 'ShippingMethodType';
  /**
   * List of channels available for the method.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  channelListings?: Maybe<Array<ShippingMethodChannelListing>>;
  /**
   * Shipping method description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: Maybe<Scalars['JSONString']['output']>;
  /**
   * List of excluded products for the shipping method.
   *
   * Requires one of the following permissions: MANAGE_SHIPPING.
   */
  excludedProducts?: Maybe<ProductCountableConnection>;
  /** Shipping method ID. */
  id: Scalars['ID']['output'];
  /** Maximum number of days for delivery. */
  maximumDeliveryDays?: Maybe<Scalars['Int']['output']>;
  /** The price of the cheapest variant (including discounts). */
  maximumOrderPrice?: Maybe<Money>;
  /** Maximum order weight to use this shipping method. */
  maximumOrderWeight?: Maybe<Weight>;
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Minimal number of days for delivery. */
  minimumDeliveryDays?: Maybe<Scalars['Int']['output']>;
  /** The price of the cheapest variant (including discounts). */
  minimumOrderPrice?: Maybe<Money>;
  /** Minimum order weight to use this shipping method. */
  minimumOrderWeight?: Maybe<Weight>;
  /** Shipping method name. */
  name: Scalars['String']['output'];
  /** Postal code ranges rule of exclusion or inclusion of the shipping method. */
  postalCodeRules?: Maybe<Array<ShippingMethodPostalCodeRule>>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * Tax class assigned to this shipping method.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  taxClass?: Maybe<TaxClass>;
  /** Returns translated shipping method fields for the given language code. */
  translation?: Maybe<ShippingMethodTranslation>;
  /** Type of the shipping method. */
  type?: Maybe<ShippingMethodTypeEnum>;
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypeExcludedProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypeMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypeMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Shipping method are the methods you'll use to get customer's orders to them. They are directly exposed to the customers. */
export type ShippingMethodTypeTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/** An enumeration. */
export enum ShippingMethodTypeEnum {
  Price = 'PRICE',
  Weight = 'WEIGHT'
}

/**
 * List of shipping methods available for the country.
 *
 * Added in Saleor 3.6.
 */
export type ShippingMethodsPerCountry = {
  __typename?: 'ShippingMethodsPerCountry';
  /** The country code. */
  countryCode: CountryCode;
  /** List of available shipping methods. */
  shippingMethods?: Maybe<Array<ShippingMethod>>;
};

export type ShippingPostalCodeRulesCreateInputRange = {
  /** End range of the postal code. */
  end?: InputMaybe<Scalars['String']['input']>;
  /** Start range of the postal code. */
  start: Scalars['String']['input'];
};

/**
 * Deletes shipping prices.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceBulkDelete = {
  __typename?: 'ShippingPriceBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
};

/**
 * Creates a new shipping price.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceCreate = {
  __typename?: 'ShippingPriceCreate';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  shippingMethod?: Maybe<ShippingMethodType>;
  /** A shipping zone to which the shipping method belongs. */
  shippingZone?: Maybe<ShippingZone>;
};

/**
 * Event sent when new shipping price is created.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceCreated = Event & {
  __typename?: 'ShippingPriceCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping method the event relates to. */
  shippingMethod?: Maybe<ShippingMethodType>;
  /** The shipping zone the shipping method belongs to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new shipping price is created.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceCreatedShippingMethodArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Event sent when new shipping price is created.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceCreatedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a shipping price.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceDelete = {
  __typename?: 'ShippingPriceDelete';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  /** A shipping method to delete. */
  shippingMethod?: Maybe<ShippingMethodType>;
  /** A shipping zone to which the shipping method belongs. */
  shippingZone?: Maybe<ShippingZone>;
};

/**
 * Event sent when shipping price is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceDeleted = Event & {
  __typename?: 'ShippingPriceDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping method the event relates to. */
  shippingMethod?: Maybe<ShippingMethodType>;
  /** The shipping zone the shipping method belongs to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when shipping price is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceDeletedShippingMethodArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Event sent when shipping price is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceDeletedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Exclude products from shipping price.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceExcludeProducts = {
  __typename?: 'ShippingPriceExcludeProducts';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  /** A shipping method with new list of excluded products. */
  shippingMethod?: Maybe<ShippingMethodType>;
};

export type ShippingPriceExcludeProductsInput = {
  /** List of products which will be excluded. */
  products: Array<Scalars['ID']['input']>;
};

export type ShippingPriceInput = {
  /** Postal code rules to add. */
  addPostalCodeRules?: InputMaybe<Array<ShippingPostalCodeRulesCreateInputRange>>;
  /** Postal code rules to delete. */
  deletePostalCodeRules?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Shipping method description. */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  /** Inclusion type for currently assigned postal code rules. */
  inclusionType?: InputMaybe<PostalCodeRuleInclusionTypeEnum>;
  /** Maximum number of days for delivery. */
  maximumDeliveryDays?: InputMaybe<Scalars['Int']['input']>;
  /** Maximum order weight to use this shipping method. */
  maximumOrderWeight?: InputMaybe<Scalars['WeightScalar']['input']>;
  /** Minimal number of days for delivery. */
  minimumDeliveryDays?: InputMaybe<Scalars['Int']['input']>;
  /** Minimum order weight to use this shipping method. */
  minimumOrderWeight?: InputMaybe<Scalars['WeightScalar']['input']>;
  /** Name of the shipping method. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Shipping zone this method belongs to. */
  shippingZone?: InputMaybe<Scalars['ID']['input']>;
  /** ID of a tax class to assign to this shipping method. If not provided, the default tax class will be used. */
  taxClass?: InputMaybe<Scalars['ID']['input']>;
  /** Shipping type: price or weight based. */
  type?: InputMaybe<ShippingMethodTypeEnum>;
};

/**
 * Remove product from excluded list for shipping price.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceRemoveProductFromExclude = {
  __typename?: 'ShippingPriceRemoveProductFromExclude';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  /** A shipping method with new list of excluded products. */
  shippingMethod?: Maybe<ShippingMethodType>;
};

/**
 * Creates/updates translations for a shipping method.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type ShippingPriceTranslate = {
  __typename?: 'ShippingPriceTranslate';
  errors: Array<TranslationError>;
  shippingMethod?: Maybe<ShippingMethodType>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type ShippingPriceTranslationInput = {
  /**
   * Translated shipping method description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Updates a new shipping price.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingPriceUpdate = {
  __typename?: 'ShippingPriceUpdate';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  shippingMethod?: Maybe<ShippingMethodType>;
  /** A shipping zone to which the shipping method belongs. */
  shippingZone?: Maybe<ShippingZone>;
};

/**
 * Event sent when shipping price is updated.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceUpdated = Event & {
  __typename?: 'ShippingPriceUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping method the event relates to. */
  shippingMethod?: Maybe<ShippingMethodType>;
  /** The shipping zone the shipping method belongs to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when shipping price is updated.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceUpdatedShippingMethodArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Event sent when shipping price is updated.
 *
 * Added in Saleor 3.2.
 */
export type ShippingPriceUpdatedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a shipping zone in the shop. Zones are the concept used only for grouping shipping methods in the dashboard, and are never exposed to the customers directly. */
export type ShippingZone = Node & ObjectWithMetadata & {
  __typename?: 'ShippingZone';
  /** List of channels for shipping zone. */
  channels: Array<Channel>;
  /** List of countries available for the method. */
  countries: Array<CountryDisplay>;
  default: Scalars['Boolean']['output'];
  /** Description of a shipping zone. */
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** Lowest and highest prices for the shipping. */
  priceRange?: Maybe<MoneyRange>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** List of shipping methods available for orders shipped to countries within this shipping zone. */
  shippingMethods?: Maybe<Array<ShippingMethodType>>;
  /** List of warehouses for shipping zone. */
  warehouses: Array<Warehouse>;
};


/** Represents a shipping zone in the shop. Zones are the concept used only for grouping shipping methods in the dashboard, and are never exposed to the customers directly. */
export type ShippingZoneMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a shipping zone in the shop. Zones are the concept used only for grouping shipping methods in the dashboard, and are never exposed to the customers directly. */
export type ShippingZoneMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents a shipping zone in the shop. Zones are the concept used only for grouping shipping methods in the dashboard, and are never exposed to the customers directly. */
export type ShippingZonePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents a shipping zone in the shop. Zones are the concept used only for grouping shipping methods in the dashboard, and are never exposed to the customers directly. */
export type ShippingZonePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Deletes shipping zones.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingZoneBulkDelete = {
  __typename?: 'ShippingZoneBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
};

export type ShippingZoneCountableConnection = {
  __typename?: 'ShippingZoneCountableConnection';
  edges: Array<ShippingZoneCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type ShippingZoneCountableEdge = {
  __typename?: 'ShippingZoneCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: ShippingZone;
};

/**
 * Creates a new shipping zone.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingZoneCreate = {
  __typename?: 'ShippingZoneCreate';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  shippingZone?: Maybe<ShippingZone>;
};

export type ShippingZoneCreateInput = {
  /** List of channels to assign to the shipping zone. */
  addChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of warehouses to assign to a shipping zone */
  addWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of countries in this shipping zone. */
  countries?: InputMaybe<Array<Scalars['String']['input']>>;
  /** Default shipping zone will be used for countries not covered by other zones. */
  default?: InputMaybe<Scalars['Boolean']['input']>;
  /** Description of the shipping zone. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Shipping zone's name. Visible only to the staff. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new shipping zone is created.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneCreated = Event & {
  __typename?: 'ShippingZoneCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping zone the event relates to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when new shipping zone is created.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneCreatedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a shipping zone.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingZoneDelete = {
  __typename?: 'ShippingZoneDelete';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  shippingZone?: Maybe<ShippingZone>;
};

/**
 * Event sent when shipping zone is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneDeleted = Event & {
  __typename?: 'ShippingZoneDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping zone the event relates to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when shipping zone is deleted.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneDeletedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export type ShippingZoneFilterInput = {
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  search?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when shipping zone metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ShippingZoneMetadataUpdated = Event & {
  __typename?: 'ShippingZoneMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping zone the event relates to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when shipping zone metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type ShippingZoneMetadataUpdatedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Updates a new shipping zone.
 *
 * Requires one of the following permissions: MANAGE_SHIPPING.
 */
export type ShippingZoneUpdate = {
  __typename?: 'ShippingZoneUpdate';
  errors: Array<ShippingError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shippingErrors: Array<ShippingError>;
  shippingZone?: Maybe<ShippingZone>;
};

export type ShippingZoneUpdateInput = {
  /** List of channels to assign to the shipping zone. */
  addChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of warehouses to assign to a shipping zone */
  addWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of countries in this shipping zone. */
  countries?: InputMaybe<Array<Scalars['String']['input']>>;
  /** Default shipping zone will be used for countries not covered by other zones. */
  default?: InputMaybe<Scalars['Boolean']['input']>;
  /** Description of the shipping zone. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Shipping zone's name. Visible only to the staff. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** List of channels to unassign from the shipping zone. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** List of warehouses to unassign from a shipping zone */
  removeWarehouses?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Event sent when shipping zone is updated.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneUpdated = Event & {
  __typename?: 'ShippingZoneUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The shipping zone the event relates to. */
  shippingZone?: Maybe<ShippingZone>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};


/**
 * Event sent when shipping zone is updated.
 *
 * Added in Saleor 3.2.
 */
export type ShippingZoneUpdatedShippingZoneArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Represents a shop resource containing general shop data and configuration. */
export type Shop = {
  __typename?: 'Shop';
  /**
   * Enable automatic fulfillment for all digital products.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  automaticFulfillmentDigitalProducts?: Maybe<Scalars['Boolean']['output']>;
  /** List of available external authentications. */
  availableExternalAuthentications: Array<ExternalAuthentication>;
  /** List of available payment gateways. */
  availablePaymentGateways: Array<PaymentGateway>;
  /** Shipping methods that are available for the shop. */
  availableShippingMethods?: Maybe<Array<ShippingMethod>>;
  /**
   * List of all currencies supported by shop's channels.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  channelCurrencies: Array<Scalars['String']['output']>;
  /**
   * Charge taxes on shipping.
   * @deprecated This field will be removed in Saleor 4.0. Use `ShippingMethodType.taxClass` to determine whether taxes are calculated for shipping methods; if a tax class is set, the taxes will be calculated, otherwise no tax rate will be applied.
   */
  chargeTaxesOnShipping: Scalars['Boolean']['output'];
  /** Company address. */
  companyAddress?: Maybe<Address>;
  /** List of countries available in the shop. */
  countries: Array<CountryDisplay>;
  /** URL of a view where customers can set their password. */
  customerSetPasswordUrl?: Maybe<Scalars['String']['output']>;
  /** Shop's default country. */
  defaultCountry?: Maybe<CountryDisplay>;
  /**
   * Default number of max downloads per digital content URL.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  defaultDigitalMaxDownloads?: Maybe<Scalars['Int']['output']>;
  /**
   * Default number of days which digital content URL will be valid.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  defaultDigitalUrlValidDays?: Maybe<Scalars['Int']['output']>;
  /**
   * Default shop's email sender's address.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  defaultMailSenderAddress?: Maybe<Scalars['String']['output']>;
  /**
   * Default shop's email sender's name.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  defaultMailSenderName?: Maybe<Scalars['String']['output']>;
  /** Default weight unit. */
  defaultWeightUnit?: Maybe<WeightUnitsEnum>;
  /** Shop's description. */
  description?: Maybe<Scalars['String']['output']>;
  /**
   * Display prices with tax in store.
   * @deprecated This field will be removed in Saleor 4.0. Use `Channel.taxConfiguration` to determine whether to display gross or net prices.
   */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** Shop's domain data. */
  domain: Domain;
  /**
   * Determines if account confirmation by email is enabled.
   *
   * Added in Saleor 3.14.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  enableAccountConfirmationByEmail?: Maybe<Scalars['Boolean']['output']>;
  /**
   * Allow to approve fulfillments which are unpaid.
   *
   * Added in Saleor 3.1.
   */
  fulfillmentAllowUnpaid: Scalars['Boolean']['output'];
  /**
   * Automatically approve all new fulfillments.
   *
   * Added in Saleor 3.1.
   */
  fulfillmentAutoApprove: Scalars['Boolean']['output'];
  /** Header text. */
  headerText?: Maybe<Scalars['String']['output']>;
  /**
   * Include taxes in prices.
   * @deprecated This field will be removed in Saleor 4.0. Use `Channel.taxConfiguration.pricesEnteredWithTax` to determine whether prices are entered with tax.
   */
  includeTaxesInPrices: Scalars['Boolean']['output'];
  /** List of the shops's supported languages. */
  languages: Array<LanguageDisplay>;
  /**
   * Default number of maximum line quantity in single checkout (per single checkout line).
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  limitQuantityPerCheckout?: Maybe<Scalars['Int']['output']>;
  /**
   * Resource limitations and current usage if any set for a shop
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
   */
  limits: LimitInfo;
  /** Shop's name. */
  name: Scalars['String']['output'];
  /** List of available permissions. */
  permissions: Array<Permission>;
  /** List of possible phone prefixes. */
  phonePrefixes: Array<Scalars['String']['output']>;
  /**
   * Default number of minutes stock will be reserved for anonymous checkout or null when stock reservation is disabled.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  reserveStockDurationAnonymousUser?: Maybe<Scalars['Int']['output']>;
  /**
   * Default number of minutes stock will be reserved for authenticated checkout or null when stock reservation is disabled.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  reserveStockDurationAuthenticatedUser?: Maybe<Scalars['Int']['output']>;
  /**
   * Minor Saleor API version.
   *
   * Added in Saleor 3.5.
   */
  schemaVersion: Scalars['String']['output'];
  /**
   * List of staff notification recipients.
   *
   * Requires one of the following permissions: MANAGE_SETTINGS.
   */
  staffNotificationRecipients?: Maybe<Array<StaffNotificationRecipient>>;
  /** Enable inventory tracking. */
  trackInventoryByDefault?: Maybe<Scalars['Boolean']['output']>;
  /** Returns translated shop fields for the given language code. */
  translation?: Maybe<ShopTranslation>;
  /**
   * Saleor API version.
   *
   * Requires one of the following permissions: AUTHENTICATED_STAFF_USER, AUTHENTICATED_APP.
   */
  version: Scalars['String']['output'];
};


/** Represents a shop resource containing general shop data and configuration. */
export type ShopAvailablePaymentGatewaysArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
  currency?: InputMaybe<Scalars['String']['input']>;
};


/** Represents a shop resource containing general shop data and configuration. */
export type ShopAvailableShippingMethodsArgs = {
  address?: InputMaybe<AddressInput>;
  channel: Scalars['String']['input'];
};


/** Represents a shop resource containing general shop data and configuration. */
export type ShopCountriesArgs = {
  filter?: InputMaybe<CountryFilterInput>;
  languageCode?: InputMaybe<LanguageCodeEnum>;
};


/** Represents a shop resource containing general shop data and configuration. */
export type ShopTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Update the shop's address. If the `null` value is passed, the currently selected address will be deleted.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type ShopAddressUpdate = {
  __typename?: 'ShopAddressUpdate';
  errors: Array<ShopError>;
  /** Updated shop. */
  shop?: Maybe<Shop>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
};

/**
 * Updates site domain of the shop.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type ShopDomainUpdate = {
  __typename?: 'ShopDomainUpdate';
  errors: Array<ShopError>;
  /** Updated shop. */
  shop?: Maybe<Shop>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
};

export type ShopError = {
  __typename?: 'ShopError';
  /** The error code. */
  code: ShopErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum ShopErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  CannotFetchTaxRates = 'CANNOT_FETCH_TAX_RATES',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

/**
 * Fetch tax rates.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type ShopFetchTaxRates = {
  __typename?: 'ShopFetchTaxRates';
  errors: Array<ShopError>;
  /** Updated shop. */
  shop?: Maybe<Shop>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
};

export type ShopSettingsInput = {
  /** Enable automatic fulfillment for all digital products. */
  automaticFulfillmentDigitalProducts?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Charge taxes on shipping.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. To enable taxes for a shipping method, assign a tax class to the shipping method with `shippingPriceCreate` or `shippingPriceUpdate` mutations.
   */
  chargeTaxesOnShipping?: InputMaybe<Scalars['Boolean']['input']>;
  /** URL of a view where customers can set their password. */
  customerSetPasswordUrl?: InputMaybe<Scalars['String']['input']>;
  /** Default number of max downloads per digital content URL. */
  defaultDigitalMaxDownloads?: InputMaybe<Scalars['Int']['input']>;
  /** Default number of days which digital content URL will be valid. */
  defaultDigitalUrlValidDays?: InputMaybe<Scalars['Int']['input']>;
  /** Default email sender's address. */
  defaultMailSenderAddress?: InputMaybe<Scalars['String']['input']>;
  /** Default email sender's name. */
  defaultMailSenderName?: InputMaybe<Scalars['String']['input']>;
  /** Default weight unit. */
  defaultWeightUnit?: InputMaybe<WeightUnitsEnum>;
  /** SEO description. */
  description?: InputMaybe<Scalars['String']['input']>;
  /**
   * Display prices with tax in store.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `taxConfigurationUpdate` mutation to configure this setting per channel or country.
   */
  displayGrossPrices?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Enable automatic account confirmation by email.
   *
   * Added in Saleor 3.14.
   */
  enableAccountConfirmationByEmail?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Enable ability to approve fulfillments which are unpaid.
   *
   * Added in Saleor 3.1.
   */
  fulfillmentAllowUnpaid?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Enable automatic approval of all new fulfillments.
   *
   * Added in Saleor 3.1.
   */
  fulfillmentAutoApprove?: InputMaybe<Scalars['Boolean']['input']>;
  /** Header text. */
  headerText?: InputMaybe<Scalars['String']['input']>;
  /**
   * Include taxes in prices.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `taxConfigurationUpdate` mutation to configure this setting per channel or country.
   */
  includeTaxesInPrices?: InputMaybe<Scalars['Boolean']['input']>;
  /**
   * Default number of maximum line quantity in single checkout. Minimum possible value is 1, default value is 50.
   *
   * Added in Saleor 3.1.
   */
  limitQuantityPerCheckout?: InputMaybe<Scalars['Int']['input']>;
  /**
   * Default number of minutes stock will be reserved for anonymous checkout. Enter 0 or null to disable.
   *
   * Added in Saleor 3.1.
   */
  reserveStockDurationAnonymousUser?: InputMaybe<Scalars['Int']['input']>;
  /**
   * Default number of minutes stock will be reserved for authenticated checkout. Enter 0 or null to disable.
   *
   * Added in Saleor 3.1.
   */
  reserveStockDurationAuthenticatedUser?: InputMaybe<Scalars['Int']['input']>;
  /** Enable inventory tracking. */
  trackInventoryByDefault?: InputMaybe<Scalars['Boolean']['input']>;
};

/**
 * Creates/updates translations for shop settings.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type ShopSettingsTranslate = {
  __typename?: 'ShopSettingsTranslate';
  errors: Array<TranslationError>;
  /** Updated shop settings. */
  shop?: Maybe<Shop>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
};

export type ShopSettingsTranslationInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  headerText?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Updates shop settings.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type ShopSettingsUpdate = {
  __typename?: 'ShopSettingsUpdate';
  errors: Array<ShopError>;
  /** Updated shop. */
  shop?: Maybe<Shop>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
};

export type ShopTranslation = Node & {
  __typename?: 'ShopTranslation';
  description: Scalars['String']['output'];
  headerText: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
};

export type SiteDomainInput = {
  /** Domain name for shop. */
  domain?: InputMaybe<Scalars['String']['input']>;
  /** Shop site name. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes staff users. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type StaffBulkDelete = {
  __typename?: 'StaffBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<StaffError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  staffErrors: Array<StaffError>;
};

/**
 * Creates a new staff user. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type StaffCreate = {
  __typename?: 'StaffCreate';
  errors: Array<StaffError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  staffErrors: Array<StaffError>;
  user?: Maybe<User>;
};

/** Fields required to create a staff user. */
export type StaffCreateInput = {
  /** List of permission group IDs to which user should be assigned. */
  addGroups?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** The unique email address of the user. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User account is active. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** A note about the user. */
  note?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** URL of a view where users should be redirected to set the password. URL in RFC 1808 format. */
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new staff user is created.
 *
 * Added in Saleor 3.5.
 */
export type StaffCreated = Event & {
  __typename?: 'StaffCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Deletes a staff user. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type StaffDelete = {
  __typename?: 'StaffDelete';
  errors: Array<StaffError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  staffErrors: Array<StaffError>;
  user?: Maybe<User>;
};

/**
 * Event sent when staff user is deleted.
 *
 * Added in Saleor 3.5.
 */
export type StaffDeleted = Event & {
  __typename?: 'StaffDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type StaffError = {
  __typename?: 'StaffError';
  /** A type of address that causes the error. */
  addressType?: Maybe<AddressTypeEnum>;
  /** The error code. */
  code: AccountErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** List of permission group IDs which cause the error. */
  groups?: Maybe<Array<Scalars['ID']['output']>>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of permissions which causes the error. */
  permissions?: Maybe<Array<PermissionEnum>>;
  /** List of user IDs which causes the error. */
  users?: Maybe<Array<Scalars['ID']['output']>>;
};

/** Represents status of a staff account. */
export enum StaffMemberStatus {
  /** User account has been activated. */
  Active = 'ACTIVE',
  /** User account has not been activated yet. */
  Deactivated = 'DEACTIVATED'
}

/** Represents a recipient of email notifications send by Saleor, such as notifications about new orders. Notifications can be assigned to staff users or arbitrary email addresses. */
export type StaffNotificationRecipient = Node & {
  __typename?: 'StaffNotificationRecipient';
  /** Determines if a notification active. */
  active?: Maybe<Scalars['Boolean']['output']>;
  /** Returns email address of a user subscribed to email notifications. */
  email?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /** Returns a user subscribed to email notifications. */
  user?: Maybe<User>;
};

/**
 * Creates a new staff notification recipient.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type StaffNotificationRecipientCreate = {
  __typename?: 'StaffNotificationRecipientCreate';
  errors: Array<ShopError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
  staffNotificationRecipient?: Maybe<StaffNotificationRecipient>;
};

/**
 * Delete staff notification recipient.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type StaffNotificationRecipientDelete = {
  __typename?: 'StaffNotificationRecipientDelete';
  errors: Array<ShopError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
  staffNotificationRecipient?: Maybe<StaffNotificationRecipient>;
};

export type StaffNotificationRecipientInput = {
  /** Determines if a notification active. */
  active?: InputMaybe<Scalars['Boolean']['input']>;
  /** Email address of a user subscribed to email notifications. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** The ID of the user subscribed to email notifications.. */
  user?: InputMaybe<Scalars['ID']['input']>;
};

/**
 * Updates a staff notification recipient.
 *
 * Requires one of the following permissions: MANAGE_SETTINGS.
 */
export type StaffNotificationRecipientUpdate = {
  __typename?: 'StaffNotificationRecipientUpdate';
  errors: Array<ShopError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  shopErrors: Array<ShopError>;
  staffNotificationRecipient?: Maybe<StaffNotificationRecipient>;
};

/**
 * Updates an existing staff user. Apps are not allowed to perform this mutation.
 *
 * Requires one of the following permissions: MANAGE_STAFF.
 */
export type StaffUpdate = {
  __typename?: 'StaffUpdate';
  errors: Array<StaffError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  staffErrors: Array<StaffError>;
  user?: Maybe<User>;
};

/** Fields required to update a staff user. */
export type StaffUpdateInput = {
  /** List of permission group IDs to which user should be assigned. */
  addGroups?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** The unique email address of the user. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User account is active. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** A note about the user. */
  note?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** List of permission group IDs from which user should be unassigned. */
  removeGroups?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Event sent when staff user is updated.
 *
 * Added in Saleor 3.5.
 */
export type StaffUpdated = Event & {
  __typename?: 'StaffUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The user the event relates to. */
  user?: Maybe<User>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type StaffUserInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  search?: InputMaybe<Scalars['String']['input']>;
  status?: InputMaybe<StaffMemberStatus>;
};

/** Represents stock. */
export type Stock = Node & {
  __typename?: 'Stock';
  id: Scalars['ID']['output'];
  productVariant: ProductVariant;
  /**
   * Quantity of a product in the warehouse's possession, including the allocated stock that is waiting for shipment.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  quantity: Scalars['Int']['output'];
  /**
   * Quantity allocated for orders.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  quantityAllocated: Scalars['Int']['output'];
  /**
   * Quantity reserved for checkouts.
   *
   * Requires one of the following permissions: MANAGE_PRODUCTS, MANAGE_ORDERS.
   */
  quantityReserved: Scalars['Int']['output'];
  warehouse: Warehouse;
};

export enum StockAvailability {
  InStock = 'IN_STOCK',
  OutOfStock = 'OUT_OF_STOCK'
}

export type StockBulkResult = {
  __typename?: 'StockBulkResult';
  /** List of errors occurred on create or update attempt. */
  errors?: Maybe<Array<StockBulkUpdateError>>;
  /** Stock data. */
  stock?: Maybe<Stock>;
};

/**
 * Updates stocks for a given variant and warehouse.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type StockBulkUpdate = {
  __typename?: 'StockBulkUpdate';
  /** Returns how many objects were updated. */
  count: Scalars['Int']['output'];
  errors: Array<StockBulkUpdateError>;
  /** List of the updated stocks. */
  results: Array<StockBulkResult>;
};

export type StockBulkUpdateError = {
  __typename?: 'StockBulkUpdateError';
  /** The error code. */
  code: StockBulkUpdateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum StockBulkUpdateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED'
}

export type StockBulkUpdateInput = {
  /** Quantity of items available for sell. */
  quantity: Scalars['Int']['input'];
  /** Variant external reference. */
  variantExternalReference?: InputMaybe<Scalars['String']['input']>;
  /** Variant ID. */
  variantId?: InputMaybe<Scalars['ID']['input']>;
  /** Warehouse external reference. */
  warehouseExternalReference?: InputMaybe<Scalars['String']['input']>;
  /** Warehouse ID. */
  warehouseId?: InputMaybe<Scalars['ID']['input']>;
};

export type StockCountableConnection = {
  __typename?: 'StockCountableConnection';
  edges: Array<StockCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type StockCountableEdge = {
  __typename?: 'StockCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Stock;
};

export type StockError = {
  __typename?: 'StockError';
  /** The error code. */
  code: StockErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum StockErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type StockFilterInput = {
  quantity?: InputMaybe<Scalars['Float']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
};

export type StockInput = {
  /** Quantity of items available for sell. */
  quantity: Scalars['Int']['input'];
  /** Warehouse in which stock is located. */
  warehouse: Scalars['ID']['input'];
};

/**
 * Represents the channel stock settings.
 *
 * Added in Saleor 3.7.
 */
export type StockSettings = {
  __typename?: 'StockSettings';
  /** Allocation strategy defines the preference of warehouses for allocations and reservations. */
  allocationStrategy: AllocationStrategyEnum;
};

export type StockSettingsInput = {
  /** Allocation strategy options. Strategy defines the preference of warehouses for allocations and reservations. */
  allocationStrategy: AllocationStrategyEnum;
};

export type StockUpdateInput = {
  /** Quantity of items available for sell. */
  quantity: Scalars['Int']['input'];
  /** Stock. */
  stock: Scalars['ID']['input'];
};

/** Enum representing the type of a payment storage in a gateway. */
export enum StorePaymentMethodEnum {
  /** Storage is disabled. The payment is not stored. */
  None = 'NONE',
  /** Off session storage type. The payment is stored to be reused even if the customer is absent. */
  OffSession = 'OFF_SESSION',
  /** On session storage type. The payment is stored only to be reused when the customer is present in the checkout flow. */
  OnSession = 'ON_SESSION'
}

/**
 * Define the filtering options for string fields.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type StringFilterInput = {
  /** The value equal to. */
  eq?: InputMaybe<Scalars['String']['input']>;
  /** The value included in. */
  oneOf?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type Subscription = {
  __typename?: 'Subscription';
  /**
   * Look up subscription event.
   *
   * Added in Saleor 3.2.
   */
  event?: Maybe<Event>;
};

export enum TaxCalculationStrategy {
  FlatRates = 'FLAT_RATES',
  TaxApp = 'TAX_APP'
}

/**
 * Tax class is a named object used to define tax rates per country. Tax class can be assigned to product types, products and shipping methods to define their tax rates.
 *
 * Added in Saleor 3.9.
 */
export type TaxClass = Node & ObjectWithMetadata & {
  __typename?: 'TaxClass';
  /** Country-specific tax rates for this tax class. */
  countries: Array<TaxClassCountryRate>;
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Name of the tax class. */
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
};


/**
 * Tax class is a named object used to define tax rates per country. Tax class can be assigned to product types, products and shipping methods to define their tax rates.
 *
 * Added in Saleor 3.9.
 */
export type TaxClassMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Tax class is a named object used to define tax rates per country. Tax class can be assigned to product types, products and shipping methods to define their tax rates.
 *
 * Added in Saleor 3.9.
 */
export type TaxClassMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/**
 * Tax class is a named object used to define tax rates per country. Tax class can be assigned to product types, products and shipping methods to define their tax rates.
 *
 * Added in Saleor 3.9.
 */
export type TaxClassPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Tax class is a named object used to define tax rates per country. Tax class can be assigned to product types, products and shipping methods to define their tax rates.
 *
 * Added in Saleor 3.9.
 */
export type TaxClassPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type TaxClassCountableConnection = {
  __typename?: 'TaxClassCountableConnection';
  edges: Array<TaxClassCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type TaxClassCountableEdge = {
  __typename?: 'TaxClassCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: TaxClass;
};

/**
 * Tax rate for a country. When tax class is null, it represents the default tax rate for that country; otherwise it's a country tax rate specific to the given tax class.
 *
 * Added in Saleor 3.9.
 */
export type TaxClassCountryRate = {
  __typename?: 'TaxClassCountryRate';
  /** Country in which this tax rate applies. */
  country: CountryDisplay;
  /** Tax rate value. */
  rate: Scalars['Float']['output'];
  /** Related tax class. */
  taxClass?: Maybe<TaxClass>;
};

/**
 * Create a tax class.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxClassCreate = {
  __typename?: 'TaxClassCreate';
  errors: Array<TaxClassCreateError>;
  taxClass?: Maybe<TaxClass>;
};

export type TaxClassCreateError = {
  __typename?: 'TaxClassCreateError';
  /** The error code. */
  code: TaxClassCreateErrorCode;
  /** List of country codes for which the configuration is invalid. */
  countryCodes: Array<Scalars['String']['output']>;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxClassCreateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

export type TaxClassCreateInput = {
  /** List of country-specific tax rates to create for this tax class. */
  createCountryRates?: InputMaybe<Array<CountryRateInput>>;
  /** Name of the tax class. */
  name: Scalars['String']['input'];
};

/**
 * Delete a tax class. After deleting the tax class any products, product types or shipping methods using it are updated to use the default tax class.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxClassDelete = {
  __typename?: 'TaxClassDelete';
  errors: Array<TaxClassDeleteError>;
  taxClass?: Maybe<TaxClass>;
};

export type TaxClassDeleteError = {
  __typename?: 'TaxClassDeleteError';
  /** The error code. */
  code: TaxClassDeleteErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxClassDeleteErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

export type TaxClassFilterInput = {
  countries?: InputMaybe<Array<CountryCode>>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
};

export type TaxClassRateInput = {
  /** Tax rate value. */
  rate?: InputMaybe<Scalars['Float']['input']>;
  /** ID of a tax class for which to update the tax rate */
  taxClassId?: InputMaybe<Scalars['ID']['input']>;
};

export enum TaxClassSortField {
  /** Sort tax classes by name. */
  Name = 'NAME'
}

export type TaxClassSortingInput = {
  /** Specifies the direction in which to sort tax classes. */
  direction: OrderDirection;
  /** Sort tax classes by the selected field. */
  field: TaxClassSortField;
};

/**
 * Update a tax class.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxClassUpdate = {
  __typename?: 'TaxClassUpdate';
  errors: Array<TaxClassUpdateError>;
  taxClass?: Maybe<TaxClass>;
};

export type TaxClassUpdateError = {
  __typename?: 'TaxClassUpdateError';
  /** The error code. */
  code: TaxClassUpdateErrorCode;
  /** List of country codes for which the configuration is invalid. */
  countryCodes: Array<Scalars['String']['output']>;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxClassUpdateErrorCode {
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

export type TaxClassUpdateInput = {
  /** Name of the tax class. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** List of country codes for which to remove the tax class rates. Note: It removes all rates for given country code. */
  removeCountryRates?: InputMaybe<Array<CountryCode>>;
  /** List of country-specific tax rates to create or update for this tax class. */
  updateCountryRates?: InputMaybe<Array<CountryRateUpdateInput>>;
};

/**
 * Channel-specific tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfiguration = Node & ObjectWithMetadata & {
  __typename?: 'TaxConfiguration';
  /** A channel to which the tax configuration applies to. */
  channel: Channel;
  /** Determines whether taxes are charged in the given channel. */
  chargeTaxes: Scalars['Boolean']['output'];
  /** List of country-specific exceptions in tax configuration. */
  countries: Array<TaxConfigurationPerCountry>;
  /** Determines whether prices displayed in a storefront should include taxes. */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /** Determines whether prices are entered with the tax included. */
  pricesEnteredWithTax: Scalars['Boolean']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /** The default strategy to use for tax calculation in the given channel. Taxes can be calculated either using user-defined flat rates or with a tax app. Empty value means that no method is selected and taxes are not calculated. */
  taxCalculationStrategy?: Maybe<TaxCalculationStrategy>;
};


/**
 * Channel-specific tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfigurationMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Channel-specific tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfigurationMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/**
 * Channel-specific tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfigurationPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Channel-specific tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfigurationPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type TaxConfigurationCountableConnection = {
  __typename?: 'TaxConfigurationCountableConnection';
  edges: Array<TaxConfigurationCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type TaxConfigurationCountableEdge = {
  __typename?: 'TaxConfigurationCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: TaxConfiguration;
};

export type TaxConfigurationFilterInput = {
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
};

/**
 * Country-specific exceptions of a channel's tax configuration.
 *
 * Added in Saleor 3.9.
 */
export type TaxConfigurationPerCountry = {
  __typename?: 'TaxConfigurationPerCountry';
  /** Determines whether taxes are charged in this country. */
  chargeTaxes: Scalars['Boolean']['output'];
  /** Country in which this configuration applies. */
  country: CountryDisplay;
  /** Determines whether prices displayed in a storefront should include taxes for this country. */
  displayGrossPrices: Scalars['Boolean']['output'];
  /** A country-specific strategy to use for tax calculation. Taxes can be calculated either using user-defined flat rates or with a tax app. If not provided, use the value from the channel's tax configuration. */
  taxCalculationStrategy?: Maybe<TaxCalculationStrategy>;
};

export type TaxConfigurationPerCountryInput = {
  /** Determines whether taxes are charged in this country. */
  chargeTaxes: Scalars['Boolean']['input'];
  /** Country in which this configuration applies. */
  countryCode: CountryCode;
  /** Determines whether prices displayed in a storefront should include taxes for this country. */
  displayGrossPrices: Scalars['Boolean']['input'];
  /** A country-specific strategy to use for tax calculation. Taxes can be calculated either using user-defined flat rates or with a tax app. If not provided, use the value from the channel's tax configuration. */
  taxCalculationStrategy?: InputMaybe<TaxCalculationStrategy>;
};

/**
 * Update tax configuration for a channel.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxConfigurationUpdate = {
  __typename?: 'TaxConfigurationUpdate';
  errors: Array<TaxConfigurationUpdateError>;
  taxConfiguration?: Maybe<TaxConfiguration>;
};

export type TaxConfigurationUpdateError = {
  __typename?: 'TaxConfigurationUpdateError';
  /** The error code. */
  code: TaxConfigurationUpdateErrorCode;
  /** List of country codes for which the configuration is invalid. */
  countryCodes: Array<Scalars['String']['output']>;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxConfigurationUpdateErrorCode {
  DuplicatedInputItem = 'DUPLICATED_INPUT_ITEM',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

export type TaxConfigurationUpdateInput = {
  /** Determines whether taxes are charged in the given channel. */
  chargeTaxes?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines whether prices displayed in a storefront should include taxes. */
  displayGrossPrices?: InputMaybe<Scalars['Boolean']['input']>;
  /** Determines whether prices are entered with the tax included. */
  pricesEnteredWithTax?: InputMaybe<Scalars['Boolean']['input']>;
  /** List of country codes for which to remove the tax configuration. */
  removeCountriesConfiguration?: InputMaybe<Array<CountryCode>>;
  /** The default strategy to use for tax calculation in the given channel. Taxes can be calculated either using user-defined flat rates or with a tax app. Empty value means that no method is selected and taxes are not calculated. */
  taxCalculationStrategy?: InputMaybe<TaxCalculationStrategy>;
  /** List of tax country configurations to create or update (identified by a country code). */
  updateCountriesConfiguration?: InputMaybe<Array<TaxConfigurationPerCountryInput>>;
};

/**
 * Tax class rates grouped by country.
 *
 * Added in Saleor 3.9.
 */
export type TaxCountryConfiguration = {
  __typename?: 'TaxCountryConfiguration';
  /** A country for which tax class rates are grouped. */
  country: CountryDisplay;
  /** List of tax class rates. */
  taxClassCountryRates: Array<TaxClassCountryRate>;
};

/**
 * Remove all tax class rates for a specific country.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxCountryConfigurationDelete = {
  __typename?: 'TaxCountryConfigurationDelete';
  errors: Array<TaxCountryConfigurationDeleteError>;
  /** Updated tax class rates grouped by a country. */
  taxCountryConfiguration?: Maybe<TaxCountryConfiguration>;
};

export type TaxCountryConfigurationDeleteError = {
  __typename?: 'TaxCountryConfigurationDeleteError';
  /** The error code. */
  code: TaxCountryConfigurationDeleteErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxCountryConfigurationDeleteErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

/**
 * Update tax class rates for a specific country.
 *
 * Added in Saleor 3.9.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxCountryConfigurationUpdate = {
  __typename?: 'TaxCountryConfigurationUpdate';
  errors: Array<TaxCountryConfigurationUpdateError>;
  /** Updated tax class rates grouped by a country. */
  taxCountryConfiguration?: Maybe<TaxCountryConfiguration>;
};

export type TaxCountryConfigurationUpdateError = {
  __typename?: 'TaxCountryConfigurationUpdateError';
  /** The error code. */
  code: TaxCountryConfigurationUpdateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of tax class IDs for which the update failed. */
  taxClassIds: Array<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxCountryConfigurationUpdateErrorCode {
  CannotCreateNegativeRate = 'CANNOT_CREATE_NEGATIVE_RATE',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  OnlyOneDefaultCountryRateAllowed = 'ONLY_ONE_DEFAULT_COUNTRY_RATE_ALLOWED'
}

/**
 * Exempt checkout or order from charging the taxes. When tax exemption is enabled, taxes won't be charged for the checkout or order. Taxes may still be calculated in cases when product prices are entered with the tax included and the net price needs to be known.
 *
 * Added in Saleor 3.8.
 *
 * Requires one of the following permissions: MANAGE_TAXES.
 */
export type TaxExemptionManage = {
  __typename?: 'TaxExemptionManage';
  errors: Array<TaxExemptionManageError>;
  taxableObject?: Maybe<TaxSourceObject>;
};

export type TaxExemptionManageError = {
  __typename?: 'TaxExemptionManageError';
  /** The error code. */
  code: TaxExemptionManageErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TaxExemptionManageErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotEditableOrder = 'NOT_EDITABLE_ORDER',
  NotFound = 'NOT_FOUND'
}

export type TaxSourceLine = CheckoutLine | OrderLine;

export type TaxSourceObject = Checkout | Order;

/** Representation of tax types fetched from tax gateway. */
export type TaxType = {
  __typename?: 'TaxType';
  /** Description of the tax type. */
  description?: Maybe<Scalars['String']['output']>;
  /** External tax code used to identify given tax group. */
  taxCode?: Maybe<Scalars['String']['output']>;
};

/** Taxable object. */
export type TaxableObject = {
  __typename?: 'TaxableObject';
  /** The address data. */
  address?: Maybe<Address>;
  channel: Channel;
  /** The currency of the object. */
  currency: Scalars['String']['output'];
  /** List of discounts. */
  discounts: Array<TaxableObjectDiscount>;
  /** List of lines assigned to the object. */
  lines: Array<TaxableObjectLine>;
  /** Determines if prices contain entered tax.. */
  pricesEnteredWithTax: Scalars['Boolean']['output'];
  /** The price of shipping method. */
  shippingPrice: Money;
  /** The source object related to this tax object. */
  sourceObject: TaxSourceObject;
};

/** Taxable object discount. */
export type TaxableObjectDiscount = {
  __typename?: 'TaxableObjectDiscount';
  /** The amount of the discount. */
  amount: Money;
  /** The name of the discount. */
  name?: Maybe<Scalars['String']['output']>;
};

export type TaxableObjectLine = {
  __typename?: 'TaxableObjectLine';
  /** Determines if taxes are being charged for the product. */
  chargeTaxes: Scalars['Boolean']['output'];
  /** The product name. */
  productName: Scalars['String']['output'];
  /** The product sku. */
  productSku?: Maybe<Scalars['String']['output']>;
  /** Number of items. */
  quantity: Scalars['Int']['output'];
  /** The source line related to this tax line. */
  sourceLine: TaxSourceLine;
  /** Price of the order line. */
  totalPrice: Money;
  /** Price of the single item in the order line. */
  unitPrice: Money;
  /** The variant name. */
  variantName: Scalars['String']['output'];
};

/** Represents a monetary value with taxes. In cases where taxes were not applied, net and gross values will be equal. */
export type TaxedMoney = {
  __typename?: 'TaxedMoney';
  /** Currency code. */
  currency: Scalars['String']['output'];
  /** Amount of money including taxes. */
  gross: Money;
  /** Amount of money without taxes. */
  net: Money;
  /** Amount of taxes. */
  tax: Money;
};

/** Represents a range of monetary values. */
export type TaxedMoneyRange = {
  __typename?: 'TaxedMoneyRange';
  /** Lower bound of a price range. */
  start?: Maybe<TaxedMoney>;
  /** Upper bound of a price range. */
  stop?: Maybe<TaxedMoney>;
};

/**
 * Event sent when thumbnail is created.
 *
 * Added in Saleor 3.12.
 */
export type ThumbnailCreated = Event & {
  __typename?: 'ThumbnailCreated';
  /**
   * Thumbnail id.
   *
   * Added in Saleor 3.12.
   */
  id?: Maybe<Scalars['ID']['output']>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /**
   * Original media url.
   *
   * Added in Saleor 3.12.
   */
  mediaUrl?: Maybe<Scalars['String']['output']>;
  /**
   * Object the thumbnail refers to.
   *
   * Added in Saleor 3.12.
   */
  objectId?: Maybe<Scalars['ID']['output']>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /**
   * Thumbnail url.
   *
   * Added in Saleor 3.12.
   */
  url?: Maybe<Scalars['String']['output']>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum ThumbnailFormatEnum {
  Avif = 'AVIF',
  Original = 'ORIGINAL',
  Webp = 'WEBP'
}

export type TimePeriod = {
  __typename?: 'TimePeriod';
  /** The length of the period. */
  amount: Scalars['Int']['output'];
  /** The type of the period. */
  type: TimePeriodTypeEnum;
};

export type TimePeriodInputType = {
  /** The length of the period. */
  amount: Scalars['Int']['input'];
  /** The type of the period. */
  type: TimePeriodTypeEnum;
};

/** An enumeration. */
export enum TimePeriodTypeEnum {
  Day = 'DAY',
  Month = 'MONTH',
  Week = 'WEEK',
  Year = 'YEAR'
}

/** An object representing a single payment. */
export type Transaction = Node & {
  __typename?: 'Transaction';
  /** Total amount of the transaction. */
  amount?: Maybe<Money>;
  created: Scalars['DateTime']['output'];
  error?: Maybe<Scalars['String']['output']>;
  gatewayResponse: Scalars['JSONString']['output'];
  id: Scalars['ID']['output'];
  isSuccess: Scalars['Boolean']['output'];
  kind: TransactionKind;
  payment: Payment;
  token: Scalars['String']['output'];
};

export type TransactionAction = {
  __typename?: 'TransactionAction';
  /** Determines the action type. */
  actionType: TransactionActionEnum;
  /** Transaction request amount. Null when action type is VOID. */
  amount?: Maybe<Scalars['PositiveDecimal']['output']>;
};

/**
 * Represents possible actions on payment transaction.
 *
 *     The following actions are possible:
 *     CHARGE - Represents the charge action.
 *     REFUND - Represents a refund action.
 *     VOID - Represents a void action. This field will be removed
 *     in Saleor 3.14 (Preview Feature). Use `CANCEL` instead.
 *     CANCEL - Represents a cancel action. Added in Saleor 3.12.
 *
 */
export enum TransactionActionEnum {
  Cancel = 'CANCEL',
  Charge = 'CHARGE',
  Refund = 'REFUND',
  Void = 'VOID'
}

/**
 * Event sent when transaction action is requested.
 *
 * Added in Saleor 3.4.
 *
 * DEPRECATED: this subscription will be removed in Saleor 3.14 (Preview Feature). Use `TransactionChargeRequested`, `TransactionRefundRequested`, `TransactionCancelationRequested` instead.
 */
export type TransactionActionRequest = Event & {
  __typename?: 'TransactionActionRequest';
  /** Requested action data. */
  action: TransactionAction;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Look up a transaction. */
  transaction?: Maybe<TransactionItem>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when transaction cancelation is requested.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionCancelationRequested = Event & {
  __typename?: 'TransactionCancelationRequested';
  /** Requested action data. */
  action: TransactionAction;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Look up a transaction. */
  transaction?: Maybe<TransactionItem>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when transaction charge is requested.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionChargeRequested = Event & {
  __typename?: 'TransactionChargeRequested';
  /** Requested action data. */
  action: TransactionAction;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Look up a transaction. */
  transaction?: Maybe<TransactionItem>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Create transaction for checkout or order.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: HANDLE_PAYMENTS.
 */
export type TransactionCreate = {
  __typename?: 'TransactionCreate';
  errors: Array<TransactionCreateError>;
  transaction?: Maybe<TransactionItem>;
};

export type TransactionCreateError = {
  __typename?: 'TransactionCreateError';
  /** The error code. */
  code: TransactionCreateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionCreateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  IncorrectCurrency = 'INCORRECT_CURRENCY',
  Invalid = 'INVALID',
  MetadataKeyRequired = 'METADATA_KEY_REQUIRED',
  NotFound = 'NOT_FOUND',
  Unique = 'UNIQUE'
}

export type TransactionCreateInput = {
  /** Amount authorized by this transaction. */
  amountAuthorized?: InputMaybe<MoneyInput>;
  /**
   * Amount canceled by this transaction.
   *
   * Added in Saleor 3.13.
   */
  amountCanceled?: InputMaybe<MoneyInput>;
  /** Amount charged by this transaction. */
  amountCharged?: InputMaybe<MoneyInput>;
  /** Amount refunded by this transaction. */
  amountRefunded?: InputMaybe<MoneyInput>;
  /**
   * Amount voided by this transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `amountCanceled` instead.
   */
  amountVoided?: InputMaybe<MoneyInput>;
  /** List of all possible actions for the transaction */
  availableActions?: InputMaybe<Array<TransactionActionEnum>>;
  /**
   * The url that will allow to redirect user to payment provider page with transaction event details.
   *
   * Added in Saleor 3.13.
   */
  externalUrl?: InputMaybe<Scalars['String']['input']>;
  /**
   * The message of the transaction.
   *
   * Added in Saleor 3.13.
   */
  message?: InputMaybe<Scalars['String']['input']>;
  /** Payment public metadata. */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Payment name of the transaction.
   *
   * Added in Saleor 3.13.
   */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Payment private metadata. */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * PSP Reference of the transaction.
   *
   * Added in Saleor 3.13.
   */
  pspReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Reference of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `pspReference` instead.
   */
  reference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Status of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). The `status` is not needed. The amounts can be used to define the current status of transactions.
   */
  status?: InputMaybe<Scalars['String']['input']>;
  /**
   * Payment type used for this transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `name` and `message` instead.
   */
  type?: InputMaybe<Scalars['String']['input']>;
};

/** Represents transaction's event. */
export type TransactionEvent = Node & {
  __typename?: 'TransactionEvent';
  /**
   * The amount related to this event.
   *
   * Added in Saleor 3.13.
   */
  amount: Money;
  createdAt: Scalars['DateTime']['output'];
  /**
   * User or App that created the transaction event.
   *
   * Added in Saleor 3.13.
   */
  createdBy?: Maybe<UserOrApp>;
  /**
   * The url that will allow to redirect user to payment provider page with transaction details.
   *
   * Added in Saleor 3.13.
   */
  externalUrl: Scalars['String']['output'];
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /**
   * Message related to the transaction's event.
   *
   * Added in Saleor 3.13.
   */
  message: Scalars['String']['output'];
  /**
   * Name of the transaction's event.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature). Use `message` instead.
   */
  name?: Maybe<Scalars['String']['output']>;
  /**
   * PSP reference of transaction.
   *
   * Added in Saleor 3.13.
   */
  pspReference: Scalars['String']['output'];
  /**
   * Reference of transaction's event.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature).Use `pspReference` instead.
   */
  reference: Scalars['String']['output'];
  /**
   * Status of transaction's event.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature). Use `type` instead.
   */
  status?: Maybe<TransactionStatus>;
  /**
   * The type of action related to this event.
   *
   * Added in Saleor 3.13.
   */
  type?: Maybe<TransactionEventTypeEnum>;
};

export type TransactionEventInput = {
  /**
   * The message related to the event.
   *
   * Added in Saleor 3.13.
   */
  message?: InputMaybe<Scalars['String']['input']>;
  /**
   * Name of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `message` instead. `name` field will be added to `message`.
   */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * PSP Reference related to this action.
   *
   * Added in Saleor 3.13.
   */
  pspReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Reference of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `pspReference` instead.
   */
  reference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Current status of the payment transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Status will be calculated by Saleor.
   */
  status?: InputMaybe<TransactionStatus>;
};

/**
 * Report the event for the transaction.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires the following permissions: OWNER and HANDLE_PAYMENTS for apps, HANDLE_PAYMENTS for staff users. Staff user cannot update a transaction that is owned by the app.
 */
export type TransactionEventReport = {
  __typename?: 'TransactionEventReport';
  /** Defines if the reported event hasn't been processed earlier. */
  alreadyProcessed?: Maybe<Scalars['Boolean']['output']>;
  errors: Array<TransactionEventReportError>;
  /** The transaction related to the reported event. */
  transaction?: Maybe<TransactionItem>;
  /** The event assigned to this report. if `alreadyProcessed` is set to `true`, the previously processed event will be returned. */
  transactionEvent?: Maybe<TransactionEvent>;
};

export type TransactionEventReportError = {
  __typename?: 'TransactionEventReportError';
  /** The error code. */
  code: TransactionEventReportErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionEventReportErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  GraphqlError = 'GRAPHQL_ERROR',
  IncorrectDetails = 'INCORRECT_DETAILS',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

/**
 * Represents possible event types.
 *
 *     Added in Saleor 3.12.
 *
 *     The following types are possible:
 *     AUTHORIZATION_SUCCESS - represents success authorization.
 *     AUTHORIZATION_FAILURE - represents failure authorization.
 *     AUTHORIZATION_ADJUSTMENT - represents authorization adjustment.
 *     AUTHORIZATION_REQUEST - represents authorization request.
 *     AUTHORIZATION_ACTION_REQUIRED - represents authorization that needs
 *     additional actions from the customer.
 *     CHARGE_ACTION_REQUIRED - represents charge that needs
 *     additional actions from the customer.
 *     CHARGE_SUCCESS - represents success charge.
 *     CHARGE_FAILURE - represents failure charge.
 *     CHARGE_BACK - represents chargeback.
 *     CHARGE_REQUEST - represents charge request.
 *     REFUND_SUCCESS - represents success refund.
 *     REFUND_FAILURE - represents failure refund.
 *     REFUND_REVERSE - represents reverse refund.
 *     REFUND_REQUEST - represents refund request.
 *     CANCEL_SUCCESS - represents success cancel.
 *     CANCEL_FAILURE - represents failure cancel.
 *     CANCEL_REQUEST - represents cancel request.
 *     INFO - represents info event.
 *
 */
export enum TransactionEventTypeEnum {
  AuthorizationActionRequired = 'AUTHORIZATION_ACTION_REQUIRED',
  AuthorizationAdjustment = 'AUTHORIZATION_ADJUSTMENT',
  AuthorizationFailure = 'AUTHORIZATION_FAILURE',
  AuthorizationRequest = 'AUTHORIZATION_REQUEST',
  AuthorizationSuccess = 'AUTHORIZATION_SUCCESS',
  CancelFailure = 'CANCEL_FAILURE',
  CancelRequest = 'CANCEL_REQUEST',
  CancelSuccess = 'CANCEL_SUCCESS',
  ChargeActionRequired = 'CHARGE_ACTION_REQUIRED',
  ChargeBack = 'CHARGE_BACK',
  ChargeFailure = 'CHARGE_FAILURE',
  ChargeRequest = 'CHARGE_REQUEST',
  ChargeSuccess = 'CHARGE_SUCCESS',
  Info = 'INFO',
  RefundFailure = 'REFUND_FAILURE',
  RefundRequest = 'REFUND_REQUEST',
  RefundReverse = 'REFUND_REVERSE',
  RefundSuccess = 'REFUND_SUCCESS'
}

/**
 * Determine the transaction flow strategy.
 *
 *     AUTHORIZATION - the processed transaction should be only authorized
 *     CHARGE - the processed transaction should be charged.
 *
 */
export enum TransactionFlowStrategyEnum {
  Authorization = 'AUTHORIZATION',
  Charge = 'CHARGE'
}

/**
 * Initializes a transaction session. It triggers the webhook `TRANSACTION_INITIALIZE_SESSION`, to the requested `paymentGateways`.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionInitialize = {
  __typename?: 'TransactionInitialize';
  /** The JSON data required to finalize the payment. */
  data?: Maybe<Scalars['JSON']['output']>;
  errors: Array<TransactionInitializeError>;
  /** The initialized transaction. */
  transaction?: Maybe<TransactionItem>;
  /** The event created for the initialized transaction. */
  transactionEvent?: Maybe<TransactionEvent>;
};

export type TransactionInitializeError = {
  __typename?: 'TransactionInitializeError';
  /** The error code. */
  code: TransactionInitializeErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionInitializeErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND'
}

/**
 * Event sent when user starts processing the payment.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionInitializeSession = Event & {
  __typename?: 'TransactionInitializeSession';
  /** Action to proceed for the transaction */
  action: TransactionProcessAction;
  /** Payment gateway data in JSON format, recieved from storefront. */
  data?: Maybe<Scalars['JSON']['output']>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Merchant reference assigned to this payment. */
  merchantReference: Scalars['String']['output'];
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Checkout or order */
  sourceObject: OrderOrCheckout;
  /** Look up a transaction. */
  transaction: TransactionItem;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Represents a payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionItem = Node & ObjectWithMetadata & {
  __typename?: 'TransactionItem';
  /** List of actions that can be performed in the current state of a payment. */
  actions: Array<TransactionActionEnum>;
  /**
   * Total amount of ongoing authorization requests for the transaction.
   *
   * Added in Saleor 3.13.
   */
  authorizePendingAmount: Money;
  /** Total amount authorized for this payment. */
  authorizedAmount: Money;
  /**
   * Total amount of ongoing cancel requests for the transaction.
   *
   * Added in Saleor 3.13.
   */
  cancelPendingAmount: Money;
  /**
   * Total amount canceled for this payment.
   *
   * Added in Saleor 3.13.
   */
  canceledAmount: Money;
  /**
   * Total amount of ongoing charge requests for the transaction.
   *
   * Added in Saleor 3.13.
   */
  chargePendingAmount: Money;
  /** Total amount charged for this payment. */
  chargedAmount: Money;
  createdAt: Scalars['DateTime']['output'];
  /**
   * User or App that created the transaction.
   *
   * Added in Saleor 3.13.
   */
  createdBy?: Maybe<UserOrApp>;
  /** List of all transaction's events. */
  events: Array<TransactionEvent>;
  /**
   * The url that will allow to redirect user to payment provider page with transaction details.
   *
   * Added in Saleor 3.13.
   */
  externalUrl: Scalars['String']['output'];
  /** The ID of the object. */
  id: Scalars['ID']['output'];
  /**
   * Message related to the transaction.
   *
   * Added in Saleor 3.13.
   */
  message: Scalars['String']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  modifiedAt: Scalars['DateTime']['output'];
  /**
   * Name of the transaction.
   *
   * Added in Saleor 3.13.
   */
  name: Scalars['String']['output'];
  /**
   * The related order.
   *
   * Added in Saleor 3.6.
   */
  order?: Maybe<Order>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * PSP reference of transaction.
   *
   * Added in Saleor 3.13.
   */
  pspReference: Scalars['String']['output'];
  /**
   * Reference of transaction.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature).Use `pspReference` instead.
   */
  reference: Scalars['String']['output'];
  /**
   * Total amount of ongoing refund requests for the transaction.
   *
   * Added in Saleor 3.13.
   */
  refundPendingAmount: Money;
  /** Total amount refunded for this payment. */
  refundedAmount: Money;
  /**
   * Status of transaction.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature). The `status` is not needed. The amounts can be used to define the current status of transactions.
   */
  status: Scalars['String']['output'];
  /**
   * Type of transaction.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature). Use `name` or `message` instead.
   */
  type: Scalars['String']['output'];
  /**
   * Total amount voided for this payment.
   * @deprecated This field will be removed in Saleor 3.14 (Preview Feature).Use `canceledAmount` instead.
   */
  voidedAmount: Money;
};


/**
 * Represents a payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionItemMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Represents a payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionItemMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/**
 * Represents a payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionItemPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/**
 * Represents a payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionItemPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Event sent when transaction item metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type TransactionItemMetadataUpdated = Event & {
  __typename?: 'TransactionItemMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Look up a transaction. */
  transaction?: Maybe<TransactionItem>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionKind {
  ActionToConfirm = 'ACTION_TO_CONFIRM',
  Auth = 'AUTH',
  Cancel = 'CANCEL',
  Capture = 'CAPTURE',
  Confirm = 'CONFIRM',
  External = 'EXTERNAL',
  Pending = 'PENDING',
  Refund = 'REFUND',
  RefundOngoing = 'REFUND_ONGOING',
  Void = 'VOID'
}

/**
 * Processes a transaction session. It triggers the webhook `TRANSACTION_PROCESS_SESSION`, to the assigned `paymentGateways`.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionProcess = {
  __typename?: 'TransactionProcess';
  /** The json data required to finalize the payment. */
  data?: Maybe<Scalars['JSON']['output']>;
  errors: Array<TransactionProcessError>;
  /** The processed transaction. */
  transaction?: Maybe<TransactionItem>;
  /** The event created for the processed transaction. */
  transactionEvent?: Maybe<TransactionEvent>;
};

export type TransactionProcessAction = {
  __typename?: 'TransactionProcessAction';
  actionType: TransactionFlowStrategyEnum;
  /** Transaction amount to process. */
  amount: Scalars['PositiveDecimal']['output'];
  /** Currency of the amount. */
  currency: Scalars['String']['output'];
};

export type TransactionProcessError = {
  __typename?: 'TransactionProcessError';
  /** The error code. */
  code: TransactionProcessErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionProcessErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  MissingPaymentApp = 'MISSING_PAYMENT_APP',
  MissingPaymentAppRelation = 'MISSING_PAYMENT_APP_RELATION',
  NotFound = 'NOT_FOUND',
  TransactionAlreadyProcessed = 'TRANSACTION_ALREADY_PROCESSED'
}

/**
 * Event sent when user has additional payment action to process.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionProcessSession = Event & {
  __typename?: 'TransactionProcessSession';
  /** Action to proceed for the transaction */
  action: TransactionProcessAction;
  /** Payment gateway data in JSON format, recieved from storefront. */
  data?: Maybe<Scalars['JSON']['output']>;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** Merchant reference assigned to this payment. */
  merchantReference: Scalars['String']['output'];
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Checkout or order */
  sourceObject: OrderOrCheckout;
  /** Look up a transaction. */
  transaction: TransactionItem;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Event sent when transaction refund is requested.
 *
 * Added in Saleor 3.13.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 */
export type TransactionRefundRequested = Event & {
  __typename?: 'TransactionRefundRequested';
  /** Requested action data. */
  action: TransactionAction;
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Look up a transaction. */
  transaction?: Maybe<TransactionItem>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

/**
 * Request an action for payment transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: HANDLE_PAYMENTS.
 */
export type TransactionRequestAction = {
  __typename?: 'TransactionRequestAction';
  errors: Array<TransactionRequestActionError>;
  transaction?: Maybe<TransactionItem>;
};

export type TransactionRequestActionError = {
  __typename?: 'TransactionRequestActionError';
  /** The error code. */
  code: TransactionRequestActionErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionRequestActionErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  MissingTransactionActionRequestWebhook = 'MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK',
  NotFound = 'NOT_FOUND'
}

/**
 * Represents a status of payment transaction.
 *
 *     The following statuses are possible:
 *     SUCCESS - Represents a sucess action.
 *     FAILURE - Represents a failure action.
 *     PENDING - Represents a pending action.
 *
 */
export enum TransactionStatus {
  Failure = 'FAILURE',
  Pending = 'PENDING',
  Success = 'SUCCESS'
}

/**
 * Update transaction.
 *
 * Added in Saleor 3.4.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires the following permissions: OWNER and HANDLE_PAYMENTS for apps, HANDLE_PAYMENTS for staff users. Staff user cannot update a transaction that is owned by the app.
 */
export type TransactionUpdate = {
  __typename?: 'TransactionUpdate';
  errors: Array<TransactionUpdateError>;
  transaction?: Maybe<TransactionItem>;
};

export type TransactionUpdateError = {
  __typename?: 'TransactionUpdateError';
  /** The error code. */
  code: TransactionUpdateErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TransactionUpdateErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  IncorrectCurrency = 'INCORRECT_CURRENCY',
  Invalid = 'INVALID',
  MetadataKeyRequired = 'METADATA_KEY_REQUIRED',
  NotFound = 'NOT_FOUND',
  Unique = 'UNIQUE'
}

export type TransactionUpdateInput = {
  /** Amount authorized by this transaction. */
  amountAuthorized?: InputMaybe<MoneyInput>;
  /**
   * Amount canceled by this transaction.
   *
   * Added in Saleor 3.13.
   */
  amountCanceled?: InputMaybe<MoneyInput>;
  /** Amount charged by this transaction. */
  amountCharged?: InputMaybe<MoneyInput>;
  /** Amount refunded by this transaction. */
  amountRefunded?: InputMaybe<MoneyInput>;
  /**
   * Amount voided by this transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `amountCanceled` instead.
   */
  amountVoided?: InputMaybe<MoneyInput>;
  /** List of all possible actions for the transaction */
  availableActions?: InputMaybe<Array<TransactionActionEnum>>;
  /**
   * The url that will allow to redirect user to payment provider page with transaction event details.
   *
   * Added in Saleor 3.13.
   */
  externalUrl?: InputMaybe<Scalars['String']['input']>;
  /**
   * The message of the transaction.
   *
   * Added in Saleor 3.13.
   */
  message?: InputMaybe<Scalars['String']['input']>;
  /** Payment public metadata. */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * Payment name of the transaction.
   *
   * Added in Saleor 3.13.
   */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Payment private metadata. */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /**
   * PSP Reference of the transaction.
   *
   * Added in Saleor 3.13.
   */
  pspReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Reference of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `pspReference` instead.
   */
  reference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Status of the transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). The `status` is not needed. The amounts can be used to define the current status of transactions.
   */
  status?: InputMaybe<Scalars['String']['input']>;
  /**
   * Payment type used for this transaction.
   *
   * DEPRECATED: this field will be removed in Saleor 3.14 (Preview Feature). Use `name` and `message` instead.
   */
  type?: InputMaybe<Scalars['String']['input']>;
};

export type TranslatableItem = AttributeTranslatableContent | AttributeValueTranslatableContent | CategoryTranslatableContent | CollectionTranslatableContent | MenuItemTranslatableContent | PageTranslatableContent | ProductTranslatableContent | ProductVariantTranslatableContent | SaleTranslatableContent | ShippingMethodTranslatableContent | VoucherTranslatableContent;

export type TranslatableItemConnection = {
  __typename?: 'TranslatableItemConnection';
  edges: Array<TranslatableItemEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type TranslatableItemEdge = {
  __typename?: 'TranslatableItemEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: TranslatableItem;
};

export enum TranslatableKinds {
  Attribute = 'ATTRIBUTE',
  AttributeValue = 'ATTRIBUTE_VALUE',
  Category = 'CATEGORY',
  Collection = 'COLLECTION',
  MenuItem = 'MENU_ITEM',
  Page = 'PAGE',
  Product = 'PRODUCT',
  Sale = 'SALE',
  ShippingMethod = 'SHIPPING_METHOD',
  Variant = 'VARIANT',
  Voucher = 'VOUCHER'
}

/**
 * Event sent when new translation is created.
 *
 * Added in Saleor 3.2.
 */
export type TranslationCreated = Event & {
  __typename?: 'TranslationCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The translation the event relates to. */
  translation?: Maybe<TranslationTypes>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type TranslationError = {
  __typename?: 'TranslationError';
  /** The error code. */
  code: TranslationErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum TranslationErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED'
}

export type TranslationInput = {
  /**
   * Translated description.
   *
   * Rich text format. For reference see https://editorjs.io/
   */
  description?: InputMaybe<Scalars['JSONString']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  seoDescription?: InputMaybe<Scalars['String']['input']>;
  seoTitle?: InputMaybe<Scalars['String']['input']>;
};

export type TranslationTypes = AttributeTranslation | AttributeValueTranslation | CategoryTranslation | CollectionTranslation | MenuItemTranslation | PageTranslation | ProductTranslation | ProductVariantTranslation | SaleTranslation | ShippingMethodTranslation | VoucherTranslation;

/**
 * Event sent when translation is updated.
 *
 * Added in Saleor 3.2.
 */
export type TranslationUpdated = Event & {
  __typename?: 'TranslationUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** The translation the event relates to. */
  translation?: Maybe<TranslationTypes>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
};

export type UpdateInvoiceInput = {
  /**
   * Fields required to update the invoice metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** Invoice number */
  number?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the invoice private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** URL of an invoice to download. */
  url?: InputMaybe<Scalars['String']['input']>;
};

/** Updates metadata of an object. To use it, you need to have access to the modified object. */
export type UpdateMetadata = {
  __typename?: 'UpdateMetadata';
  errors: Array<MetadataError>;
  item?: Maybe<ObjectWithMetadata>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  metadataErrors: Array<MetadataError>;
};

/** Updates private metadata of an object. To use it, you need to be an authenticated staff user or an app and have access to the modified object. */
export type UpdatePrivateMetadata = {
  __typename?: 'UpdatePrivateMetadata';
  errors: Array<MetadataError>;
  item?: Maybe<ObjectWithMetadata>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  metadataErrors: Array<MetadataError>;
};

export type UploadError = {
  __typename?: 'UploadError';
  /** The error code. */
  code: UploadErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum UploadErrorCode {
  GraphqlError = 'GRAPHQL_ERROR'
}

/** Represents user data. */
export type User = Node & ObjectWithMetadata & {
  __typename?: 'User';
  /**
   * List of channels the user has access to. The sum of channels from all user groups. If at least one group has `restrictedAccessToChannels` set to False - all channels are returned.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  accessibleChannels?: Maybe<Array<Channel>>;
  /** List of all user's addresses. */
  addresses: Array<Address>;
  avatar?: Maybe<Image>;
  /**
   * Returns the last open checkout of this user.
   * @deprecated This field will be removed in Saleor 4.0. Use the `checkoutTokens` field to fetch the user checkouts.
   */
  checkout?: Maybe<Checkout>;
  /** Returns the checkout ID's assigned to this user. */
  checkoutIds?: Maybe<Array<Scalars['ID']['output']>>;
  /**
   * Returns the checkout UUID's assigned to this user.
   * @deprecated This field will be removed in Saleor 4.0. Use `checkoutIds` instead.
   */
  checkoutTokens?: Maybe<Array<Scalars['UUID']['output']>>;
  /**
   * Returns checkouts assigned to this user.
   *
   * Added in Saleor 3.8.
   */
  checkouts?: Maybe<CheckoutCountableConnection>;
  dateJoined: Scalars['DateTime']['output'];
  defaultBillingAddress?: Maybe<Address>;
  defaultShippingAddress?: Maybe<Address>;
  /** List of user's permission groups which user can manage. */
  editableGroups?: Maybe<Array<Group>>;
  email: Scalars['String']['output'];
  /**
   * List of events associated with the user.
   *
   * Requires one of the following permissions: MANAGE_USERS, MANAGE_STAFF.
   */
  events?: Maybe<Array<CustomerEvent>>;
  /**
   * External ID of this user.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  firstName: Scalars['String']['output'];
  /** List of the user gift cards. */
  giftCards?: Maybe<GiftCardCountableConnection>;
  id: Scalars['ID']['output'];
  isActive: Scalars['Boolean']['output'];
  isStaff: Scalars['Boolean']['output'];
  /** User language code. */
  languageCode: LanguageCodeEnum;
  lastLogin?: Maybe<Scalars['DateTime']['output']>;
  lastName: Scalars['String']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * A note about the customer.
   *
   * Requires one of the following permissions: MANAGE_USERS, MANAGE_STAFF.
   */
  note?: Maybe<Scalars['String']['output']>;
  /** List of user's orders. Requires one of the following permissions: MANAGE_STAFF, OWNER. */
  orders?: Maybe<OrderCountableConnection>;
  /** List of user's permission groups. */
  permissionGroups?: Maybe<Array<Group>>;
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * Determine if user have restricted access to channels. False if at least one user group has `restrictedAccessToChannels` set to False.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  restrictedAccessToChannels: Scalars['Boolean']['output'];
  /** List of stored payment sources. */
  storedPaymentSources?: Maybe<Array<PaymentSource>>;
  updatedAt: Scalars['DateTime']['output'];
  /** List of user's permissions. */
  userPermissions?: Maybe<Array<UserPermission>>;
};


/** Represents user data. */
export type UserAvatarArgs = {
  format?: InputMaybe<ThumbnailFormatEnum>;
  size?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents user data. */
export type UserCheckoutIdsArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};


/** Represents user data. */
export type UserCheckoutTokensArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};


/** Represents user data. */
export type UserCheckoutsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  channel?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents user data. */
export type UserGiftCardsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents user data. */
export type UserMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents user data. */
export type UserMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents user data. */
export type UserOrdersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Represents user data. */
export type UserPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents user data. */
export type UserPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents user data. */
export type UserStoredPaymentSourcesArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a user avatar. Only for staff members.
 *
 * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
 */
export type UserAvatarDelete = {
  __typename?: 'UserAvatarDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** An updated user instance. */
  user?: Maybe<User>;
};

/**
 * Create a user avatar. Only for staff members. This mutation must be sent as a `multipart` request. More detailed specs of the upload format can be found here: https://github.com/jaydenseric/graphql-multipart-request-spec
 *
 * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
 */
export type UserAvatarUpdate = {
  __typename?: 'UserAvatarUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** An updated user instance. */
  user?: Maybe<User>;
};

/**
 * Activate or deactivate users.
 *
 * Requires one of the following permissions: MANAGE_USERS.
 */
export type UserBulkSetActive = {
  __typename?: 'UserBulkSetActive';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  errors: Array<AccountError>;
};

export type UserCountableConnection = {
  __typename?: 'UserCountableConnection';
  edges: Array<UserCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type UserCountableEdge = {
  __typename?: 'UserCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: User;
};

export type UserCreateInput = {
  /** Slug of a channel which will be used for notify user. Optional when only one channel exists. */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Billing address of the customer. */
  defaultBillingAddress?: InputMaybe<AddressInput>;
  /** Shipping address of the customer. */
  defaultShippingAddress?: InputMaybe<AddressInput>;
  /** The unique email address of the user. */
  email?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of the customer.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Given name. */
  firstName?: InputMaybe<Scalars['String']['input']>;
  /** User account is active. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** User language code. */
  languageCode?: InputMaybe<LanguageCodeEnum>;
  /** Family name. */
  lastName?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user metadata.
   *
   * Added in Saleor 3.14.
   */
  metadata?: InputMaybe<Array<MetadataInput>>;
  /** A note about the user. */
  note?: InputMaybe<Scalars['String']['input']>;
  /**
   * Fields required to update the user private metadata.
   *
   * Added in Saleor 3.14.
   */
  privateMetadata?: InputMaybe<Array<MetadataInput>>;
  /** URL of a view where users should be redirected to set the password. URL in RFC 1808 format. */
  redirectUrl?: InputMaybe<Scalars['String']['input']>;
};

export type UserOrApp = App | User;

/** Represents user's permissions. */
export type UserPermission = {
  __typename?: 'UserPermission';
  /** Internal code for permission. */
  code: PermissionEnum;
  /** Describe action(s) allowed to do by permission. */
  name: Scalars['String']['output'];
  /** List of user permission groups which contains this permission. */
  sourcePermissionGroups?: Maybe<Array<Group>>;
};


/** Represents user's permissions. */
export type UserPermissionSourcePermissionGroupsArgs = {
  userId: Scalars['ID']['input'];
};

export enum UserSortField {
  /** Sort users by created at. */
  CreatedAt = 'CREATED_AT',
  /** Sort users by email. */
  Email = 'EMAIL',
  /** Sort users by first name. */
  FirstName = 'FIRST_NAME',
  /** Sort users by last modified at. */
  LastModifiedAt = 'LAST_MODIFIED_AT',
  /** Sort users by last name. */
  LastName = 'LAST_NAME',
  /** Sort users by order count. */
  OrderCount = 'ORDER_COUNT'
}

export type UserSortingInput = {
  /** Specifies the direction in which to sort users. */
  direction: OrderDirection;
  /** Sort users by the selected field. */
  field: UserSortField;
};

/** Represents a VAT rate for a country. */
export type Vat = {
  __typename?: 'VAT';
  /** Country code. */
  countryCode: Scalars['String']['output'];
  /** Country's VAT rate exceptions for specific types of goods. */
  reducedRates: Array<ReducedRate>;
  /** Standard VAT rate in percent. */
  standardRate?: Maybe<Scalars['Float']['output']>;
};

export enum VariantAttributeScope {
  All = 'ALL',
  NotVariantSelection = 'NOT_VARIANT_SELECTION',
  VariantSelection = 'VARIANT_SELECTION'
}

/**
 * Assign an media to a product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type VariantMediaAssign = {
  __typename?: 'VariantMediaAssign';
  errors: Array<ProductError>;
  media?: Maybe<ProductMedia>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productVariant?: Maybe<ProductVariant>;
};

/**
 * Unassign an media from a product variant.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type VariantMediaUnassign = {
  __typename?: 'VariantMediaUnassign';
  errors: Array<ProductError>;
  media?: Maybe<ProductMedia>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  productErrors: Array<ProductError>;
  productVariant?: Maybe<ProductVariant>;
};

/** Represents availability of a variant in the storefront. */
export type VariantPricingInfo = {
  __typename?: 'VariantPricingInfo';
  /** The discount amount if in sale (null otherwise). */
  discount?: Maybe<TaxedMoney>;
  /** The discount amount in the local currency. */
  discountLocalCurrency?: Maybe<TaxedMoney>;
  /** Whether it is in sale or not. */
  onSale?: Maybe<Scalars['Boolean']['output']>;
  /** The price, with any discount subtracted. */
  price?: Maybe<TaxedMoney>;
  /** The discounted price in the local currency. */
  priceLocalCurrency?: Maybe<TaxedMoney>;
  /** The price without any discount. */
  priceUndiscounted?: Maybe<TaxedMoney>;
};

/** Verify JWT token. */
export type VerifyToken = {
  __typename?: 'VerifyToken';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  accountErrors: Array<AccountError>;
  errors: Array<AccountError>;
  /** Determine if token is valid or not. */
  isValid: Scalars['Boolean']['output'];
  /** JWT payload. */
  payload?: Maybe<Scalars['GenericScalar']['output']>;
  /** User assigned to token. */
  user?: Maybe<User>;
};

/** An enumeration. */
export enum VolumeUnitsEnum {
  AcreFt = 'ACRE_FT',
  AcreIn = 'ACRE_IN',
  CubicCentimeter = 'CUBIC_CENTIMETER',
  CubicDecimeter = 'CUBIC_DECIMETER',
  CubicFoot = 'CUBIC_FOOT',
  CubicInch = 'CUBIC_INCH',
  CubicMeter = 'CUBIC_METER',
  CubicMillimeter = 'CUBIC_MILLIMETER',
  CubicYard = 'CUBIC_YARD',
  FlOz = 'FL_OZ',
  Liter = 'LITER',
  Pint = 'PINT',
  Qt = 'QT'
}

/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type Voucher = Node & ObjectWithMetadata & {
  __typename?: 'Voucher';
  applyOncePerCustomer: Scalars['Boolean']['output'];
  applyOncePerOrder: Scalars['Boolean']['output'];
  /** List of categories this voucher applies to. */
  categories?: Maybe<CategoryCountableConnection>;
  /**
   * List of availability in channels for the voucher.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  channelListings?: Maybe<Array<VoucherChannelListing>>;
  code: Scalars['String']['output'];
  /**
   * List of collections this voucher applies to.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  collections?: Maybe<CollectionCountableConnection>;
  /** List of countries available for the shipping voucher. */
  countries?: Maybe<Array<CountryDisplay>>;
  /** Currency code for voucher. */
  currency?: Maybe<Scalars['String']['output']>;
  /** Voucher value. */
  discountValue?: Maybe<Scalars['Float']['output']>;
  /** Determines a type of discount for voucher - value or percentage */
  discountValueType: DiscountValueTypeEnum;
  endDate?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  minCheckoutItemsQuantity?: Maybe<Scalars['Int']['output']>;
  /** Minimum order value to apply voucher. */
  minSpent?: Maybe<Money>;
  name?: Maybe<Scalars['String']['output']>;
  onlyForStaff: Scalars['Boolean']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  /**
   * List of products this voucher applies to.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  products?: Maybe<ProductCountableConnection>;
  startDate: Scalars['DateTime']['output'];
  /** Returns translated voucher fields for the given language code. */
  translation?: Maybe<VoucherTranslation>;
  /** Determines a type of voucher. */
  type: VoucherTypeEnum;
  usageLimit?: Maybe<Scalars['Int']['output']>;
  used: Scalars['Int']['output'];
  /**
   * List of product variants this voucher applies to.
   *
   * Added in Saleor 3.1.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   */
  variants?: Maybe<ProductVariantCountableConnection>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherCategoriesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherCollectionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherPrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherPrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherProductsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherTranslationArgs = {
  languageCode: LanguageCodeEnum;
};


/** Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes. */
export type VoucherVariantsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};

/**
 * Adds products, categories, collections to a voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherAddCatalogues = {
  __typename?: 'VoucherAddCatalogues';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** Voucher of which catalogue IDs will be modified. */
  voucher?: Maybe<Voucher>;
};

/**
 * Deletes vouchers.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherBulkDelete = {
  __typename?: 'VoucherBulkDelete';
  /** Returns how many objects were affected. */
  count: Scalars['Int']['output'];
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
};

/** Represents voucher channel listing. */
export type VoucherChannelListing = Node & {
  __typename?: 'VoucherChannelListing';
  channel: Channel;
  currency: Scalars['String']['output'];
  discountValue: Scalars['Float']['output'];
  id: Scalars['ID']['output'];
  minSpent?: Maybe<Money>;
};

export type VoucherChannelListingAddInput = {
  /** ID of a channel. */
  channelId: Scalars['ID']['input'];
  /** Value of the voucher. */
  discountValue?: InputMaybe<Scalars['PositiveDecimal']['input']>;
  /** Min purchase amount required to apply the voucher. */
  minAmountSpent?: InputMaybe<Scalars['PositiveDecimal']['input']>;
};

export type VoucherChannelListingInput = {
  /** List of channels to which the voucher should be assigned. */
  addChannels?: InputMaybe<Array<VoucherChannelListingAddInput>>;
  /** List of channels from which the voucher should be unassigned. */
  removeChannels?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Manage voucher's availability in channels.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherChannelListingUpdate = {
  __typename?: 'VoucherChannelListingUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** An updated voucher instance. */
  voucher?: Maybe<Voucher>;
};

export type VoucherCountableConnection = {
  __typename?: 'VoucherCountableConnection';
  edges: Array<VoucherCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type VoucherCountableEdge = {
  __typename?: 'VoucherCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Voucher;
};

/**
 * Creates a new voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherCreate = {
  __typename?: 'VoucherCreate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  voucher?: Maybe<Voucher>;
};

/**
 * Event sent when new voucher is created.
 *
 * Added in Saleor 3.4.
 */
export type VoucherCreated = Event & {
  __typename?: 'VoucherCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The voucher the event relates to. */
  voucher?: Maybe<Voucher>;
};


/**
 * Event sent when new voucher is created.
 *
 * Added in Saleor 3.4.
 */
export type VoucherCreatedVoucherArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Deletes a voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherDelete = {
  __typename?: 'VoucherDelete';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  voucher?: Maybe<Voucher>;
};

/**
 * Event sent when voucher is deleted.
 *
 * Added in Saleor 3.4.
 */
export type VoucherDeleted = Event & {
  __typename?: 'VoucherDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The voucher the event relates to. */
  voucher?: Maybe<Voucher>;
};


/**
 * Event sent when voucher is deleted.
 *
 * Added in Saleor 3.4.
 */
export type VoucherDeletedVoucherArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

export enum VoucherDiscountType {
  Fixed = 'FIXED',
  Percentage = 'PERCENTAGE',
  Shipping = 'SHIPPING'
}

export type VoucherFilterInput = {
  discountType?: InputMaybe<Array<VoucherDiscountType>>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  metadata?: InputMaybe<Array<MetadataFilter>>;
  search?: InputMaybe<Scalars['String']['input']>;
  started?: InputMaybe<DateTimeRangeInput>;
  status?: InputMaybe<Array<DiscountStatusEnum>>;
  timesUsed?: InputMaybe<IntRangeInput>;
};

export type VoucherInput = {
  /** Voucher should be applied once per customer. */
  applyOncePerCustomer?: InputMaybe<Scalars['Boolean']['input']>;
  /** Voucher should be applied to the cheapest item or entire order. */
  applyOncePerOrder?: InputMaybe<Scalars['Boolean']['input']>;
  /** Categories discounted by the voucher. */
  categories?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Code to use the voucher. */
  code?: InputMaybe<Scalars['String']['input']>;
  /** Collections discounted by the voucher. */
  collections?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Country codes that can be used with the shipping voucher. */
  countries?: InputMaybe<Array<Scalars['String']['input']>>;
  /** Choices: fixed or percentage. */
  discountValueType?: InputMaybe<DiscountValueTypeEnum>;
  /** End date of the voucher in ISO 8601 format. */
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** Minimal quantity of checkout items required to apply the voucher. */
  minCheckoutItemsQuantity?: InputMaybe<Scalars['Int']['input']>;
  /** Voucher name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Voucher can be used only by staff user. */
  onlyForStaff?: InputMaybe<Scalars['Boolean']['input']>;
  /** Products discounted by the voucher. */
  products?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Start date of the voucher in ISO 8601 format. */
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** Voucher type: PRODUCT, CATEGORY SHIPPING or ENTIRE_ORDER. */
  type?: InputMaybe<VoucherTypeEnum>;
  /** Limit number of times this voucher can be used in total. */
  usageLimit?: InputMaybe<Scalars['Int']['input']>;
  /**
   * Variants discounted by the voucher.
   *
   * Added in Saleor 3.1.
   */
  variants?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/**
 * Event sent when voucher metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type VoucherMetadataUpdated = Event & {
  __typename?: 'VoucherMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The voucher the event relates to. */
  voucher?: Maybe<Voucher>;
};


/**
 * Event sent when voucher metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type VoucherMetadataUpdatedVoucherArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Removes products, categories, collections from a voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherRemoveCatalogues = {
  __typename?: 'VoucherRemoveCatalogues';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  /** Voucher of which catalogue IDs will be modified. */
  voucher?: Maybe<Voucher>;
};

export enum VoucherSortField {
  /** Sort vouchers by code. */
  Code = 'CODE',
  /** Sort vouchers by end date. */
  EndDate = 'END_DATE',
  /**
   * Sort vouchers by minimum spent amount.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  MinimumSpentAmount = 'MINIMUM_SPENT_AMOUNT',
  /** Sort vouchers by start date. */
  StartDate = 'START_DATE',
  /** Sort vouchers by type. */
  Type = 'TYPE',
  /** Sort vouchers by usage limit. */
  UsageLimit = 'USAGE_LIMIT',
  /**
   * Sort vouchers by value.
   *
   * This option requires a channel filter to work as the values can vary between channels.
   */
  Value = 'VALUE'
}

export type VoucherSortingInput = {
  /**
   * Specifies the channel in which to sort the data.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use root-level channel argument instead.
   */
  channel?: InputMaybe<Scalars['String']['input']>;
  /** Specifies the direction in which to sort vouchers. */
  direction: OrderDirection;
  /** Sort vouchers by the selected field. */
  field: VoucherSortField;
};

export type VoucherTranslatableContent = Node & {
  __typename?: 'VoucherTranslatableContent';
  id: Scalars['ID']['output'];
  name?: Maybe<Scalars['String']['output']>;
  /** Returns translated voucher fields for the given language code. */
  translation?: Maybe<VoucherTranslation>;
  /**
   * Vouchers allow giving discounts to particular customers on categories, collections or specific products. They can be used during checkout by providing valid voucher codes.
   *
   * Requires one of the following permissions: MANAGE_DISCOUNTS.
   * @deprecated This field will be removed in Saleor 4.0. Get model fields from the root level queries.
   */
  voucher?: Maybe<Voucher>;
};


export type VoucherTranslatableContentTranslationArgs = {
  languageCode: LanguageCodeEnum;
};

/**
 * Creates/updates translations for a voucher.
 *
 * Requires one of the following permissions: MANAGE_TRANSLATIONS.
 */
export type VoucherTranslate = {
  __typename?: 'VoucherTranslate';
  errors: Array<TranslationError>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  translationErrors: Array<TranslationError>;
  voucher?: Maybe<Voucher>;
};

export type VoucherTranslation = Node & {
  __typename?: 'VoucherTranslation';
  id: Scalars['ID']['output'];
  /** Translation language. */
  language: LanguageDisplay;
  name?: Maybe<Scalars['String']['output']>;
};

export enum VoucherTypeEnum {
  EntireOrder = 'ENTIRE_ORDER',
  Shipping = 'SHIPPING',
  SpecificProduct = 'SPECIFIC_PRODUCT'
}

/**
 * Updates a voucher.
 *
 * Requires one of the following permissions: MANAGE_DISCOUNTS.
 */
export type VoucherUpdate = {
  __typename?: 'VoucherUpdate';
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  discountErrors: Array<DiscountError>;
  errors: Array<DiscountError>;
  voucher?: Maybe<Voucher>;
};

/**
 * Event sent when voucher is updated.
 *
 * Added in Saleor 3.4.
 */
export type VoucherUpdated = Event & {
  __typename?: 'VoucherUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The voucher the event relates to. */
  voucher?: Maybe<Voucher>;
};


/**
 * Event sent when voucher is updated.
 *
 * Added in Saleor 3.4.
 */
export type VoucherUpdatedVoucherArgs = {
  channel?: InputMaybe<Scalars['String']['input']>;
};

/** Represents warehouse. */
export type Warehouse = Node & ObjectWithMetadata & {
  __typename?: 'Warehouse';
  address: Address;
  /**
   * Click and collect options: local, all or disabled.
   *
   * Added in Saleor 3.1.
   */
  clickAndCollectOption: WarehouseClickAndCollectOptionEnum;
  /**
   * Warehouse company name.
   * @deprecated This field will be removed in Saleor 4.0. Use `Address.companyName` instead.
   */
  companyName: Scalars['String']['output'];
  email: Scalars['String']['output'];
  /**
   * External ID of this warehouse.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  isPrivate: Scalars['Boolean']['output'];
  /** List of public metadata items. Can be accessed without permissions. */
  metadata: Array<MetadataItem>;
  /**
   * A single key from public metadata.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafield?: Maybe<Scalars['String']['output']>;
  /**
   * Public metadata. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  metafields?: Maybe<Scalars['Metadata']['output']>;
  name: Scalars['String']['output'];
  /** List of private metadata items. Requires staff permissions to access. */
  privateMetadata: Array<MetadataItem>;
  /**
   * A single key from private metadata. Requires staff permissions to access.
   *
   * Tip: Use GraphQL aliases to fetch multiple keys.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafield?: Maybe<Scalars['String']['output']>;
  /**
   * Private metadata. Requires staff permissions to access. Use `keys` to control which fields you want to include. The default is to include everything.
   *
   * Added in Saleor 3.3.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  privateMetafields?: Maybe<Scalars['Metadata']['output']>;
  shippingZones: ShippingZoneCountableConnection;
  slug: Scalars['String']['output'];
};


/** Represents warehouse. */
export type WarehouseMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents warehouse. */
export type WarehouseMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents warehouse. */
export type WarehousePrivateMetafieldArgs = {
  key: Scalars['String']['input'];
};


/** Represents warehouse. */
export type WarehousePrivateMetafieldsArgs = {
  keys?: InputMaybe<Array<Scalars['String']['input']>>;
};


/** Represents warehouse. */
export type WarehouseShippingZonesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
};

/** An enumeration. */
export enum WarehouseClickAndCollectOptionEnum {
  All = 'ALL',
  Disabled = 'DISABLED',
  Local = 'LOCAL'
}

export type WarehouseCountableConnection = {
  __typename?: 'WarehouseCountableConnection';
  edges: Array<WarehouseCountableEdge>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  /** A total count of items in the collection. */
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type WarehouseCountableEdge = {
  __typename?: 'WarehouseCountableEdge';
  /** A cursor for use in pagination. */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge. */
  node: Warehouse;
};

/**
 * Creates new warehouse.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type WarehouseCreate = {
  __typename?: 'WarehouseCreate';
  errors: Array<WarehouseError>;
  warehouse?: Maybe<Warehouse>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  warehouseErrors: Array<WarehouseError>;
};

export type WarehouseCreateInput = {
  /** Address of the warehouse. */
  address: AddressInput;
  /** The email address of the warehouse. */
  email?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of the warehouse.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /** Warehouse name. */
  name: Scalars['String']['input'];
  /**
   * Shipping zones supported by the warehouse.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Providing the zone ids will raise a ValidationError.
   */
  shippingZones?: InputMaybe<Array<Scalars['ID']['input']>>;
  /** Warehouse slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when new warehouse is created.
 *
 * Added in Saleor 3.4.
 */
export type WarehouseCreated = Event & {
  __typename?: 'WarehouseCreated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The warehouse the event relates to. */
  warehouse?: Maybe<Warehouse>;
};

/**
 * Deletes selected warehouse.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type WarehouseDelete = {
  __typename?: 'WarehouseDelete';
  errors: Array<WarehouseError>;
  warehouse?: Maybe<Warehouse>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  warehouseErrors: Array<WarehouseError>;
};

/**
 * Event sent when warehouse is deleted.
 *
 * Added in Saleor 3.4.
 */
export type WarehouseDeleted = Event & {
  __typename?: 'WarehouseDeleted';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The warehouse the event relates to. */
  warehouse?: Maybe<Warehouse>;
};

export type WarehouseError = {
  __typename?: 'WarehouseError';
  /** The error code. */
  code: WarehouseErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
  /** List of shipping zones IDs which causes the error. */
  shippingZones?: Maybe<Array<Scalars['ID']['output']>>;
};

/** An enumeration. */
export enum WarehouseErrorCode {
  AlreadyExists = 'ALREADY_EXISTS',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Unique = 'UNIQUE'
}

export type WarehouseFilterInput = {
  channels?: InputMaybe<Array<Scalars['ID']['input']>>;
  clickAndCollectOption?: InputMaybe<WarehouseClickAndCollectOptionEnum>;
  ids?: InputMaybe<Array<Scalars['ID']['input']>>;
  isPrivate?: InputMaybe<Scalars['Boolean']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
  slugs?: InputMaybe<Array<Scalars['String']['input']>>;
};

/**
 * Event sent when warehouse metadata is updated.
 *
 * Added in Saleor 3.8.
 */
export type WarehouseMetadataUpdated = Event & {
  __typename?: 'WarehouseMetadataUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The warehouse the event relates to. */
  warehouse?: Maybe<Warehouse>;
};

/**
 * Add shipping zone to given warehouse.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type WarehouseShippingZoneAssign = {
  __typename?: 'WarehouseShippingZoneAssign';
  errors: Array<WarehouseError>;
  warehouse?: Maybe<Warehouse>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  warehouseErrors: Array<WarehouseError>;
};

/**
 * Remove shipping zone from given warehouse.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type WarehouseShippingZoneUnassign = {
  __typename?: 'WarehouseShippingZoneUnassign';
  errors: Array<WarehouseError>;
  warehouse?: Maybe<Warehouse>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  warehouseErrors: Array<WarehouseError>;
};

export enum WarehouseSortField {
  /** Sort warehouses by name. */
  Name = 'NAME'
}

export type WarehouseSortingInput = {
  /** Specifies the direction in which to sort warehouses. */
  direction: OrderDirection;
  /** Sort warehouses by the selected field. */
  field: WarehouseSortField;
};

/**
 * Updates given warehouse.
 *
 * Requires one of the following permissions: MANAGE_PRODUCTS.
 */
export type WarehouseUpdate = {
  __typename?: 'WarehouseUpdate';
  errors: Array<WarehouseError>;
  warehouse?: Maybe<Warehouse>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  warehouseErrors: Array<WarehouseError>;
};

export type WarehouseUpdateInput = {
  /** Address of the warehouse. */
  address?: InputMaybe<AddressInput>;
  /**
   * Click and collect options: local, all or disabled.
   *
   * Added in Saleor 3.1.
   */
  clickAndCollectOption?: InputMaybe<WarehouseClickAndCollectOptionEnum>;
  /** The email address of the warehouse. */
  email?: InputMaybe<Scalars['String']['input']>;
  /**
   * External ID of the warehouse.
   *
   * Added in Saleor 3.10.
   */
  externalReference?: InputMaybe<Scalars['String']['input']>;
  /**
   * Visibility of warehouse stocks.
   *
   * Added in Saleor 3.1.
   */
  isPrivate?: InputMaybe<Scalars['Boolean']['input']>;
  /** Warehouse name. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** Warehouse slug. */
  slug?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Event sent when warehouse is updated.
 *
 * Added in Saleor 3.4.
 */
export type WarehouseUpdated = Event & {
  __typename?: 'WarehouseUpdated';
  /** Time of the event. */
  issuedAt?: Maybe<Scalars['DateTime']['output']>;
  /** The user or application that triggered the event. */
  issuingPrincipal?: Maybe<IssuingPrincipal>;
  /** The application receiving the webhook. */
  recipient?: Maybe<App>;
  /** Saleor version that triggered the event. */
  version?: Maybe<Scalars['String']['output']>;
  /** The warehouse the event relates to. */
  warehouse?: Maybe<Warehouse>;
};

/** Webhook. */
export type Webhook = Node & {
  __typename?: 'Webhook';
  app: App;
  /** List of asynchronous webhook events. */
  asyncEvents: Array<WebhookEventAsync>;
  /**
   * Custom headers, which will be added to HTTP request.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  customHeaders?: Maybe<Scalars['JSONString']['output']>;
  /** Event deliveries. */
  eventDeliveries?: Maybe<EventDeliveryCountableConnection>;
  /**
   * List of webhook events.
   * @deprecated This field will be removed in Saleor 4.0. Use `asyncEvents` or `syncEvents` instead.
   */
  events: Array<WebhookEvent>;
  id: Scalars['ID']['output'];
  /** Informs if webhook is activated. */
  isActive: Scalars['Boolean']['output'];
  name: Scalars['String']['output'];
  /**
   * Used to create a hash signature for each payload.
   * @deprecated This field will be removed in Saleor 4.0. As of Saleor 3.5, webhook payloads default to signing using a verifiable JWS.
   */
  secretKey?: Maybe<Scalars['String']['output']>;
  /** Used to define payloads for specific events. */
  subscriptionQuery?: Maybe<Scalars['String']['output']>;
  /** List of synchronous webhook events. */
  syncEvents: Array<WebhookEventSync>;
  /** Target URL for webhook. */
  targetUrl: Scalars['String']['output'];
};


/** Webhook. */
export type WebhookEventDeliveriesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  filter?: InputMaybe<EventDeliveryFilterInput>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  sortBy?: InputMaybe<EventDeliverySortingInput>;
};

/**
 * Creates a new webhook subscription.
 *
 * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
 */
export type WebhookCreate = {
  __typename?: 'WebhookCreate';
  errors: Array<WebhookError>;
  webhook?: Maybe<Webhook>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  webhookErrors: Array<WebhookError>;
};

export type WebhookCreateInput = {
  /** ID of the app to which webhook belongs. */
  app?: InputMaybe<Scalars['ID']['input']>;
  /** The asynchronous events that webhook wants to subscribe. */
  asyncEvents?: InputMaybe<Array<WebhookEventTypeAsyncEnum>>;
  /**
   * Custom headers, which will be added to HTTP request. There is a limitation of 5 headers per webhook and 998 characters per header.Only "X-*" and "Authorization*" keys are allowed.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  customHeaders?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * The events that webhook wants to subscribe.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `asyncEvents` or `syncEvents` instead.
   */
  events?: InputMaybe<Array<WebhookEventTypeEnum>>;
  /** Determine if webhook will be set active or not. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** The name of the webhook. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Subscription query used to define a webhook payload.
   *
   * Added in Saleor 3.2.
   */
  query?: InputMaybe<Scalars['String']['input']>;
  /**
   * The secret key used to create a hash signature with each payload.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. As of Saleor 3.5, webhook payloads default to signing using a verifiable JWS.
   */
  secretKey?: InputMaybe<Scalars['String']['input']>;
  /** The synchronous events that webhook wants to subscribe. */
  syncEvents?: InputMaybe<Array<WebhookEventTypeSyncEnum>>;
  /** The url to receive the payload. */
  targetUrl?: InputMaybe<Scalars['String']['input']>;
};

/**
 * Delete a webhook. Before the deletion, the webhook is deactivated to pause any deliveries that are already scheduled. The deletion might fail if delivery is in progress. In such a case, the webhook is not deleted but remains deactivated.
 *
 * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
 */
export type WebhookDelete = {
  __typename?: 'WebhookDelete';
  errors: Array<WebhookError>;
  webhook?: Maybe<Webhook>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  webhookErrors: Array<WebhookError>;
};

/**
 * Performs a dry run of a webhook event. Supports a single event (the first, if multiple provided in the `query`). Requires permission relevant to processed event.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
 */
export type WebhookDryRun = {
  __typename?: 'WebhookDryRun';
  errors: Array<WebhookDryRunError>;
  /** JSON payload, that would be sent out to webhook's target URL. */
  payload?: Maybe<Scalars['JSONString']['output']>;
};

export type WebhookDryRunError = {
  __typename?: 'WebhookDryRunError';
  /** The error code. */
  code: WebhookDryRunErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum WebhookDryRunErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  InvalidId = 'INVALID_ID',
  MissingEvent = 'MISSING_EVENT',
  MissingPermission = 'MISSING_PERMISSION',
  MissingSubscription = 'MISSING_SUBSCRIPTION',
  NotFound = 'NOT_FOUND',
  Syntax = 'SYNTAX',
  TypeNotSupported = 'TYPE_NOT_SUPPORTED',
  UnableToParse = 'UNABLE_TO_PARSE'
}

export type WebhookError = {
  __typename?: 'WebhookError';
  /** The error code. */
  code: WebhookErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum WebhookErrorCode {
  DeleteFailed = 'DELETE_FAILED',
  GraphqlError = 'GRAPHQL_ERROR',
  Invalid = 'INVALID',
  InvalidCustomHeaders = 'INVALID_CUSTOM_HEADERS',
  MissingEvent = 'MISSING_EVENT',
  MissingSubscription = 'MISSING_SUBSCRIPTION',
  NotFound = 'NOT_FOUND',
  Required = 'REQUIRED',
  Syntax = 'SYNTAX',
  UnableToParse = 'UNABLE_TO_PARSE',
  Unique = 'UNIQUE'
}

/** Webhook event. */
export type WebhookEvent = {
  __typename?: 'WebhookEvent';
  /** Internal name of the event type. */
  eventType: WebhookEventTypeEnum;
  /** Display name of the event. */
  name: Scalars['String']['output'];
};

/** Asynchronous webhook event. */
export type WebhookEventAsync = {
  __typename?: 'WebhookEventAsync';
  /** Internal name of the event type. */
  eventType: WebhookEventTypeAsyncEnum;
  /** Display name of the event. */
  name: Scalars['String']['output'];
};

/** Synchronous webhook event. */
export type WebhookEventSync = {
  __typename?: 'WebhookEventSync';
  /** Internal name of the event type. */
  eventType: WebhookEventTypeSyncEnum;
  /** Display name of the event. */
  name: Scalars['String']['output'];
};

/** Enum determining type of webhook. */
export enum WebhookEventTypeAsyncEnum {
  /** A new address created. */
  AddressCreated = 'ADDRESS_CREATED',
  /** An address deleted. */
  AddressDeleted = 'ADDRESS_DELETED',
  /** An address updated. */
  AddressUpdated = 'ADDRESS_UPDATED',
  /** All the events. */
  AnyEvents = 'ANY_EVENTS',
  /** An app deleted. */
  AppDeleted = 'APP_DELETED',
  /** A new app installed. */
  AppInstalled = 'APP_INSTALLED',
  /** An app status is changed. */
  AppStatusChanged = 'APP_STATUS_CHANGED',
  /** An app updated. */
  AppUpdated = 'APP_UPDATED',
  /** A new attribute is created. */
  AttributeCreated = 'ATTRIBUTE_CREATED',
  /** An attribute is deleted. */
  AttributeDeleted = 'ATTRIBUTE_DELETED',
  /** An attribute is updated. */
  AttributeUpdated = 'ATTRIBUTE_UPDATED',
  /** A new attribute value is created. */
  AttributeValueCreated = 'ATTRIBUTE_VALUE_CREATED',
  /** An attribute value is deleted. */
  AttributeValueDeleted = 'ATTRIBUTE_VALUE_DELETED',
  /** An attribute value is updated. */
  AttributeValueUpdated = 'ATTRIBUTE_VALUE_UPDATED',
  /** A new category created. */
  CategoryCreated = 'CATEGORY_CREATED',
  /** A category is deleted. */
  CategoryDeleted = 'CATEGORY_DELETED',
  /** A category is updated. */
  CategoryUpdated = 'CATEGORY_UPDATED',
  /** A new channel created. */
  ChannelCreated = 'CHANNEL_CREATED',
  /** A channel is deleted. */
  ChannelDeleted = 'CHANNEL_DELETED',
  /** A channel status is changed. */
  ChannelStatusChanged = 'CHANNEL_STATUS_CHANGED',
  /** A channel is updated. */
  ChannelUpdated = 'CHANNEL_UPDATED',
  /** A new checkout is created. */
  CheckoutCreated = 'CHECKOUT_CREATED',
  CheckoutFullyPaid = 'CHECKOUT_FULLY_PAID',
  /**
   * A checkout metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CheckoutMetadataUpdated = 'CHECKOUT_METADATA_UPDATED',
  /** A checkout is updated. It also triggers all updates related to the checkout. */
  CheckoutUpdated = 'CHECKOUT_UPDATED',
  /** A new collection is created. */
  CollectionCreated = 'COLLECTION_CREATED',
  /** A collection is deleted. */
  CollectionDeleted = 'COLLECTION_DELETED',
  /**
   * A collection metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CollectionMetadataUpdated = 'COLLECTION_METADATA_UPDATED',
  /** A collection is updated. */
  CollectionUpdated = 'COLLECTION_UPDATED',
  /** A new customer account is created. */
  CustomerCreated = 'CUSTOMER_CREATED',
  /** A customer account is deleted. */
  CustomerDeleted = 'CUSTOMER_DELETED',
  /**
   * A customer account metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CustomerMetadataUpdated = 'CUSTOMER_METADATA_UPDATED',
  /** A customer account is updated. */
  CustomerUpdated = 'CUSTOMER_UPDATED',
  /** A draft order is created. */
  DraftOrderCreated = 'DRAFT_ORDER_CREATED',
  /** A draft order is deleted. */
  DraftOrderDeleted = 'DRAFT_ORDER_DELETED',
  /** A draft order is updated. */
  DraftOrderUpdated = 'DRAFT_ORDER_UPDATED',
  /** A fulfillment is approved. */
  FulfillmentApproved = 'FULFILLMENT_APPROVED',
  /** A fulfillment is cancelled. */
  FulfillmentCanceled = 'FULFILLMENT_CANCELED',
  /** A new fulfillment is created. */
  FulfillmentCreated = 'FULFILLMENT_CREATED',
  /**
   * A fulfillment metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  FulfillmentMetadataUpdated = 'FULFILLMENT_METADATA_UPDATED',
  /** A new gift card created. */
  GiftCardCreated = 'GIFT_CARD_CREATED',
  /** A gift card is deleted. */
  GiftCardDeleted = 'GIFT_CARD_DELETED',
  /**
   * A gift card metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  GiftCardMetadataUpdated = 'GIFT_CARD_METADATA_UPDATED',
  /**
   * A gift card has been sent.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  GiftCardSent = 'GIFT_CARD_SENT',
  /** A gift card status is changed. */
  GiftCardStatusChanged = 'GIFT_CARD_STATUS_CHANGED',
  /** A gift card is updated. */
  GiftCardUpdated = 'GIFT_CARD_UPDATED',
  /** An invoice is deleted. */
  InvoiceDeleted = 'INVOICE_DELETED',
  /** An invoice for order requested. */
  InvoiceRequested = 'INVOICE_REQUESTED',
  /** Invoice has been sent. */
  InvoiceSent = 'INVOICE_SENT',
  /** A new menu created. */
  MenuCreated = 'MENU_CREATED',
  /** A menu is deleted. */
  MenuDeleted = 'MENU_DELETED',
  /** A new menu item created. */
  MenuItemCreated = 'MENU_ITEM_CREATED',
  /** A menu item is deleted. */
  MenuItemDeleted = 'MENU_ITEM_DELETED',
  /** A menu item is updated. */
  MenuItemUpdated = 'MENU_ITEM_UPDATED',
  /** A menu is updated. */
  MenuUpdated = 'MENU_UPDATED',
  /** User notification triggered. */
  NotifyUser = 'NOTIFY_USER',
  /** An observability event is created. */
  Observability = 'OBSERVABILITY',
  /** An order is cancelled. */
  OrderCancelled = 'ORDER_CANCELLED',
  /** An order is confirmed (status change unconfirmed -> unfulfilled) by a staff user using the OrderConfirm mutation. It also triggers when the user completes the checkout and the shop setting `automatically_confirm_all_new_orders` is enabled. */
  OrderConfirmed = 'ORDER_CONFIRMED',
  /** A new order is placed. */
  OrderCreated = 'ORDER_CREATED',
  /** An order is expired. */
  OrderExpired = 'ORDER_EXPIRED',
  /** An order is fulfilled. */
  OrderFulfilled = 'ORDER_FULFILLED',
  /** Payment is made and an order is fully paid. */
  OrderFullyPaid = 'ORDER_FULLY_PAID',
  /**
   * The order is fully refunded.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderFullyRefunded = 'ORDER_FULLY_REFUNDED',
  /**
   * An order metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  OrderMetadataUpdated = 'ORDER_METADATA_UPDATED',
  /**
   * Payment has been made. The order may be partially or fully paid.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderPaid = 'ORDER_PAID',
  /**
   * The order received a refund. The order may be partially or fully refunded.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderRefunded = 'ORDER_REFUNDED',
  /** An order is updated; triggered for all changes related to an order; covers all other order webhooks, except for ORDER_CREATED. */
  OrderUpdated = 'ORDER_UPDATED',
  /** A new page is created. */
  PageCreated = 'PAGE_CREATED',
  /** A page is deleted. */
  PageDeleted = 'PAGE_DELETED',
  /** A new page type is created. */
  PageTypeCreated = 'PAGE_TYPE_CREATED',
  /** A page type is deleted. */
  PageTypeDeleted = 'PAGE_TYPE_DELETED',
  /** A page type is updated. */
  PageTypeUpdated = 'PAGE_TYPE_UPDATED',
  /** A page is updated. */
  PageUpdated = 'PAGE_UPDATED',
  /** A new permission group is created. */
  PermissionGroupCreated = 'PERMISSION_GROUP_CREATED',
  /** A permission group is deleted. */
  PermissionGroupDeleted = 'PERMISSION_GROUP_DELETED',
  /** A permission group is updated. */
  PermissionGroupUpdated = 'PERMISSION_GROUP_UPDATED',
  /** A new product is created. */
  ProductCreated = 'PRODUCT_CREATED',
  /** A product is deleted. */
  ProductDeleted = 'PRODUCT_DELETED',
  /**
   * A new product media is created.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaCreated = 'PRODUCT_MEDIA_CREATED',
  /**
   * A product media is deleted.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaDeleted = 'PRODUCT_MEDIA_DELETED',
  /**
   * A product media is updated.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaUpdated = 'PRODUCT_MEDIA_UPDATED',
  /**
   * A product metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ProductMetadataUpdated = 'PRODUCT_METADATA_UPDATED',
  /** A product is updated. */
  ProductUpdated = 'PRODUCT_UPDATED',
  /** A product variant is back in stock. */
  ProductVariantBackInStock = 'PRODUCT_VARIANT_BACK_IN_STOCK',
  /** A new product variant is created. */
  ProductVariantCreated = 'PRODUCT_VARIANT_CREATED',
  /** A product variant is deleted. */
  ProductVariantDeleted = 'PRODUCT_VARIANT_DELETED',
  /**
   * A product variant metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ProductVariantMetadataUpdated = 'PRODUCT_VARIANT_METADATA_UPDATED',
  /** A product variant is out of stock. */
  ProductVariantOutOfStock = 'PRODUCT_VARIANT_OUT_OF_STOCK',
  /** A product variant stock is updated */
  ProductVariantStockUpdated = 'PRODUCT_VARIANT_STOCK_UPDATED',
  /** A product variant is updated. */
  ProductVariantUpdated = 'PRODUCT_VARIANT_UPDATED',
  /** A sale is created. */
  SaleCreated = 'SALE_CREATED',
  /** A sale is deleted. */
  SaleDeleted = 'SALE_DELETED',
  /** A sale is activated or deactivated. */
  SaleToggle = 'SALE_TOGGLE',
  /** A sale is updated. */
  SaleUpdated = 'SALE_UPDATED',
  /** A new shipping price is created. */
  ShippingPriceCreated = 'SHIPPING_PRICE_CREATED',
  /** A shipping price is deleted. */
  ShippingPriceDeleted = 'SHIPPING_PRICE_DELETED',
  /** A shipping price is updated. */
  ShippingPriceUpdated = 'SHIPPING_PRICE_UPDATED',
  /** A new shipping zone is created. */
  ShippingZoneCreated = 'SHIPPING_ZONE_CREATED',
  /** A shipping zone is deleted. */
  ShippingZoneDeleted = 'SHIPPING_ZONE_DELETED',
  /**
   * A shipping zone metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ShippingZoneMetadataUpdated = 'SHIPPING_ZONE_METADATA_UPDATED',
  /** A shipping zone is updated. */
  ShippingZoneUpdated = 'SHIPPING_ZONE_UPDATED',
  /** A new staff user is created. */
  StaffCreated = 'STAFF_CREATED',
  /** A staff user is deleted. */
  StaffDeleted = 'STAFF_DELETED',
  /** A staff user is updated. */
  StaffUpdated = 'STAFF_UPDATED',
  /**
   * A thumbnail is created.
   *
   * Added in Saleor 3.12.
   */
  ThumbnailCreated = 'THUMBNAIL_CREATED',
  /**
   * An action requested for transaction.
   *
   * DEPRECATED: this subscription will be removed in Saleor 3.14 (Preview Feature). Use `TRANSACTION_CHARGE_REQUESTED`, `TRANSACTION_REFUND_REQUESTED`, `TRANSACTION_CANCELATION_REQUESTED` instead.
   */
  TransactionActionRequest = 'TRANSACTION_ACTION_REQUEST',
  /**
   * Transaction item metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  TransactionItemMetadataUpdated = 'TRANSACTION_ITEM_METADATA_UPDATED',
  /** A new translation is created. */
  TranslationCreated = 'TRANSLATION_CREATED',
  /** A translation is updated. */
  TranslationUpdated = 'TRANSLATION_UPDATED',
  /** A new voucher created. */
  VoucherCreated = 'VOUCHER_CREATED',
  /** A voucher is deleted. */
  VoucherDeleted = 'VOUCHER_DELETED',
  /**
   * A voucher metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  VoucherMetadataUpdated = 'VOUCHER_METADATA_UPDATED',
  /** A voucher is updated. */
  VoucherUpdated = 'VOUCHER_UPDATED',
  /** A new warehouse created. */
  WarehouseCreated = 'WAREHOUSE_CREATED',
  /** A warehouse is deleted. */
  WarehouseDeleted = 'WAREHOUSE_DELETED',
  /**
   * A warehouse metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  WarehouseMetadataUpdated = 'WAREHOUSE_METADATA_UPDATED',
  /** A warehouse is updated. */
  WarehouseUpdated = 'WAREHOUSE_UPDATED'
}

/** Enum determining type of webhook. */
export enum WebhookEventTypeEnum {
  /** A new address created. */
  AddressCreated = 'ADDRESS_CREATED',
  /** An address deleted. */
  AddressDeleted = 'ADDRESS_DELETED',
  /** An address updated. */
  AddressUpdated = 'ADDRESS_UPDATED',
  /** All the events. */
  AnyEvents = 'ANY_EVENTS',
  /** An app deleted. */
  AppDeleted = 'APP_DELETED',
  /** A new app installed. */
  AppInstalled = 'APP_INSTALLED',
  /** An app status is changed. */
  AppStatusChanged = 'APP_STATUS_CHANGED',
  /** An app updated. */
  AppUpdated = 'APP_UPDATED',
  /** A new attribute is created. */
  AttributeCreated = 'ATTRIBUTE_CREATED',
  /** An attribute is deleted. */
  AttributeDeleted = 'ATTRIBUTE_DELETED',
  /** An attribute is updated. */
  AttributeUpdated = 'ATTRIBUTE_UPDATED',
  /** A new attribute value is created. */
  AttributeValueCreated = 'ATTRIBUTE_VALUE_CREATED',
  /** An attribute value is deleted. */
  AttributeValueDeleted = 'ATTRIBUTE_VALUE_DELETED',
  /** An attribute value is updated. */
  AttributeValueUpdated = 'ATTRIBUTE_VALUE_UPDATED',
  /** A new category created. */
  CategoryCreated = 'CATEGORY_CREATED',
  /** A category is deleted. */
  CategoryDeleted = 'CATEGORY_DELETED',
  /** A category is updated. */
  CategoryUpdated = 'CATEGORY_UPDATED',
  /** A new channel created. */
  ChannelCreated = 'CHANNEL_CREATED',
  /** A channel is deleted. */
  ChannelDeleted = 'CHANNEL_DELETED',
  /** A channel status is changed. */
  ChannelStatusChanged = 'CHANNEL_STATUS_CHANGED',
  /** A channel is updated. */
  ChannelUpdated = 'CHANNEL_UPDATED',
  /**
   * Event called for checkout tax calculation.
   *
   * Added in Saleor 3.6.
   */
  CheckoutCalculateTaxes = 'CHECKOUT_CALCULATE_TAXES',
  /** A new checkout is created. */
  CheckoutCreated = 'CHECKOUT_CREATED',
  /** Filter shipping methods for checkout. */
  CheckoutFilterShippingMethods = 'CHECKOUT_FILTER_SHIPPING_METHODS',
  CheckoutFullyPaid = 'CHECKOUT_FULLY_PAID',
  /**
   * A checkout metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CheckoutMetadataUpdated = 'CHECKOUT_METADATA_UPDATED',
  /** A checkout is updated. It also triggers all updates related to the checkout. */
  CheckoutUpdated = 'CHECKOUT_UPDATED',
  /** A new collection is created. */
  CollectionCreated = 'COLLECTION_CREATED',
  /** A collection is deleted. */
  CollectionDeleted = 'COLLECTION_DELETED',
  /**
   * A collection metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CollectionMetadataUpdated = 'COLLECTION_METADATA_UPDATED',
  /** A collection is updated. */
  CollectionUpdated = 'COLLECTION_UPDATED',
  /** A new customer account is created. */
  CustomerCreated = 'CUSTOMER_CREATED',
  /** A customer account is deleted. */
  CustomerDeleted = 'CUSTOMER_DELETED',
  /**
   * A customer account metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  CustomerMetadataUpdated = 'CUSTOMER_METADATA_UPDATED',
  /** A customer account is updated. */
  CustomerUpdated = 'CUSTOMER_UPDATED',
  /** A draft order is created. */
  DraftOrderCreated = 'DRAFT_ORDER_CREATED',
  /** A draft order is deleted. */
  DraftOrderDeleted = 'DRAFT_ORDER_DELETED',
  /** A draft order is updated. */
  DraftOrderUpdated = 'DRAFT_ORDER_UPDATED',
  /** A fulfillment is approved. */
  FulfillmentApproved = 'FULFILLMENT_APPROVED',
  /** A fulfillment is cancelled. */
  FulfillmentCanceled = 'FULFILLMENT_CANCELED',
  /** A new fulfillment is created. */
  FulfillmentCreated = 'FULFILLMENT_CREATED',
  /**
   * A fulfillment metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  FulfillmentMetadataUpdated = 'FULFILLMENT_METADATA_UPDATED',
  /** A new gift card created. */
  GiftCardCreated = 'GIFT_CARD_CREATED',
  /** A gift card is deleted. */
  GiftCardDeleted = 'GIFT_CARD_DELETED',
  /**
   * A gift card metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  GiftCardMetadataUpdated = 'GIFT_CARD_METADATA_UPDATED',
  /**
   * A gift card has been sent.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  GiftCardSent = 'GIFT_CARD_SENT',
  /** A gift card status is changed. */
  GiftCardStatusChanged = 'GIFT_CARD_STATUS_CHANGED',
  /** A gift card is updated. */
  GiftCardUpdated = 'GIFT_CARD_UPDATED',
  /** An invoice is deleted. */
  InvoiceDeleted = 'INVOICE_DELETED',
  /** An invoice for order requested. */
  InvoiceRequested = 'INVOICE_REQUESTED',
  /** Invoice has been sent. */
  InvoiceSent = 'INVOICE_SENT',
  /** A new menu created. */
  MenuCreated = 'MENU_CREATED',
  /** A menu is deleted. */
  MenuDeleted = 'MENU_DELETED',
  /** A new menu item created. */
  MenuItemCreated = 'MENU_ITEM_CREATED',
  /** A menu item is deleted. */
  MenuItemDeleted = 'MENU_ITEM_DELETED',
  /** A menu item is updated. */
  MenuItemUpdated = 'MENU_ITEM_UPDATED',
  /** A menu is updated. */
  MenuUpdated = 'MENU_UPDATED',
  /** User notification triggered. */
  NotifyUser = 'NOTIFY_USER',
  /** An observability event is created. */
  Observability = 'OBSERVABILITY',
  /**
   * Event called for order tax calculation.
   *
   * Added in Saleor 3.6.
   */
  OrderCalculateTaxes = 'ORDER_CALCULATE_TAXES',
  /** An order is cancelled. */
  OrderCancelled = 'ORDER_CANCELLED',
  /** An order is confirmed (status change unconfirmed -> unfulfilled) by a staff user using the OrderConfirm mutation. It also triggers when the user completes the checkout and the shop setting `automatically_confirm_all_new_orders` is enabled. */
  OrderConfirmed = 'ORDER_CONFIRMED',
  /** A new order is placed. */
  OrderCreated = 'ORDER_CREATED',
  /** An order is expired. */
  OrderExpired = 'ORDER_EXPIRED',
  /** Filter shipping methods for order. */
  OrderFilterShippingMethods = 'ORDER_FILTER_SHIPPING_METHODS',
  /** An order is fulfilled. */
  OrderFulfilled = 'ORDER_FULFILLED',
  /** Payment is made and an order is fully paid. */
  OrderFullyPaid = 'ORDER_FULLY_PAID',
  /**
   * The order is fully refunded.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderFullyRefunded = 'ORDER_FULLY_REFUNDED',
  /**
   * An order metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  OrderMetadataUpdated = 'ORDER_METADATA_UPDATED',
  /**
   * Payment has been made. The order may be partially or fully paid.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderPaid = 'ORDER_PAID',
  /**
   * The order received a refund. The order may be partially or fully refunded.
   *
   * Added in Saleor 3.14.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  OrderRefunded = 'ORDER_REFUNDED',
  /** An order is updated; triggered for all changes related to an order; covers all other order webhooks, except for ORDER_CREATED. */
  OrderUpdated = 'ORDER_UPDATED',
  /** A new page is created. */
  PageCreated = 'PAGE_CREATED',
  /** A page is deleted. */
  PageDeleted = 'PAGE_DELETED',
  /** A new page type is created. */
  PageTypeCreated = 'PAGE_TYPE_CREATED',
  /** A page type is deleted. */
  PageTypeDeleted = 'PAGE_TYPE_DELETED',
  /** A page type is updated. */
  PageTypeUpdated = 'PAGE_TYPE_UPDATED',
  /** A page is updated. */
  PageUpdated = 'PAGE_UPDATED',
  /** Authorize payment. */
  PaymentAuthorize = 'PAYMENT_AUTHORIZE',
  /** Capture payment. */
  PaymentCapture = 'PAYMENT_CAPTURE',
  /** Confirm payment. */
  PaymentConfirm = 'PAYMENT_CONFIRM',
  PaymentGatewayInitializeSession = 'PAYMENT_GATEWAY_INITIALIZE_SESSION',
  /** Listing available payment gateways. */
  PaymentListGateways = 'PAYMENT_LIST_GATEWAYS',
  /** Process payment. */
  PaymentProcess = 'PAYMENT_PROCESS',
  /** Refund payment. */
  PaymentRefund = 'PAYMENT_REFUND',
  /** Void payment. */
  PaymentVoid = 'PAYMENT_VOID',
  /** A new permission group is created. */
  PermissionGroupCreated = 'PERMISSION_GROUP_CREATED',
  /** A permission group is deleted. */
  PermissionGroupDeleted = 'PERMISSION_GROUP_DELETED',
  /** A permission group is updated. */
  PermissionGroupUpdated = 'PERMISSION_GROUP_UPDATED',
  /** A new product is created. */
  ProductCreated = 'PRODUCT_CREATED',
  /** A product is deleted. */
  ProductDeleted = 'PRODUCT_DELETED',
  /**
   * A new product media is created.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaCreated = 'PRODUCT_MEDIA_CREATED',
  /**
   * A product media is deleted.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaDeleted = 'PRODUCT_MEDIA_DELETED',
  /**
   * A product media is updated.
   *
   * Added in Saleor 3.12.
   */
  ProductMediaUpdated = 'PRODUCT_MEDIA_UPDATED',
  /**
   * A product metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ProductMetadataUpdated = 'PRODUCT_METADATA_UPDATED',
  /** A product is updated. */
  ProductUpdated = 'PRODUCT_UPDATED',
  /** A product variant is back in stock. */
  ProductVariantBackInStock = 'PRODUCT_VARIANT_BACK_IN_STOCK',
  /** A new product variant is created. */
  ProductVariantCreated = 'PRODUCT_VARIANT_CREATED',
  /** A product variant is deleted. */
  ProductVariantDeleted = 'PRODUCT_VARIANT_DELETED',
  /**
   * A product variant metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ProductVariantMetadataUpdated = 'PRODUCT_VARIANT_METADATA_UPDATED',
  /** A product variant is out of stock. */
  ProductVariantOutOfStock = 'PRODUCT_VARIANT_OUT_OF_STOCK',
  /** A product variant stock is updated */
  ProductVariantStockUpdated = 'PRODUCT_VARIANT_STOCK_UPDATED',
  /** A product variant is updated. */
  ProductVariantUpdated = 'PRODUCT_VARIANT_UPDATED',
  /** A sale is created. */
  SaleCreated = 'SALE_CREATED',
  /** A sale is deleted. */
  SaleDeleted = 'SALE_DELETED',
  /** A sale is activated or deactivated. */
  SaleToggle = 'SALE_TOGGLE',
  /** A sale is updated. */
  SaleUpdated = 'SALE_UPDATED',
  /** Fetch external shipping methods for checkout. */
  ShippingListMethodsForCheckout = 'SHIPPING_LIST_METHODS_FOR_CHECKOUT',
  /** A new shipping price is created. */
  ShippingPriceCreated = 'SHIPPING_PRICE_CREATED',
  /** A shipping price is deleted. */
  ShippingPriceDeleted = 'SHIPPING_PRICE_DELETED',
  /** A shipping price is updated. */
  ShippingPriceUpdated = 'SHIPPING_PRICE_UPDATED',
  /** A new shipping zone is created. */
  ShippingZoneCreated = 'SHIPPING_ZONE_CREATED',
  /** A shipping zone is deleted. */
  ShippingZoneDeleted = 'SHIPPING_ZONE_DELETED',
  /**
   * A shipping zone metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  ShippingZoneMetadataUpdated = 'SHIPPING_ZONE_METADATA_UPDATED',
  /** A shipping zone is updated. */
  ShippingZoneUpdated = 'SHIPPING_ZONE_UPDATED',
  /** A new staff user is created. */
  StaffCreated = 'STAFF_CREATED',
  /** A staff user is deleted. */
  StaffDeleted = 'STAFF_DELETED',
  /** A staff user is updated. */
  StaffUpdated = 'STAFF_UPDATED',
  /**
   * A thumbnail is created.
   *
   * Added in Saleor 3.12.
   */
  ThumbnailCreated = 'THUMBNAIL_CREATED',
  /**
   * An action requested for transaction.
   *
   * DEPRECATED: this subscription will be removed in Saleor 3.14 (Preview Feature). Use `TRANSACTION_CHARGE_REQUESTED`, `TRANSACTION_REFUND_REQUESTED`, `TRANSACTION_CANCELATION_REQUESTED` instead.
   */
  TransactionActionRequest = 'TRANSACTION_ACTION_REQUEST',
  /**
   * Event called when cancel has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionCancelationRequested = 'TRANSACTION_CANCELATION_REQUESTED',
  /**
   * Event called when charge has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionChargeRequested = 'TRANSACTION_CHARGE_REQUESTED',
  TransactionInitializeSession = 'TRANSACTION_INITIALIZE_SESSION',
  /**
   * Transaction item metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  TransactionItemMetadataUpdated = 'TRANSACTION_ITEM_METADATA_UPDATED',
  TransactionProcessSession = 'TRANSACTION_PROCESS_SESSION',
  /**
   * Event called when refund has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionRefundRequested = 'TRANSACTION_REFUND_REQUESTED',
  /** A new translation is created. */
  TranslationCreated = 'TRANSLATION_CREATED',
  /** A translation is updated. */
  TranslationUpdated = 'TRANSLATION_UPDATED',
  /** A new voucher created. */
  VoucherCreated = 'VOUCHER_CREATED',
  /** A voucher is deleted. */
  VoucherDeleted = 'VOUCHER_DELETED',
  /**
   * A voucher metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  VoucherMetadataUpdated = 'VOUCHER_METADATA_UPDATED',
  /** A voucher is updated. */
  VoucherUpdated = 'VOUCHER_UPDATED',
  /** A new warehouse created. */
  WarehouseCreated = 'WAREHOUSE_CREATED',
  /** A warehouse is deleted. */
  WarehouseDeleted = 'WAREHOUSE_DELETED',
  /**
   * A warehouse metadata is updated.
   *
   * Added in Saleor 3.8.
   */
  WarehouseMetadataUpdated = 'WAREHOUSE_METADATA_UPDATED',
  /** A warehouse is updated. */
  WarehouseUpdated = 'WAREHOUSE_UPDATED'
}

/** Enum determining type of webhook. */
export enum WebhookEventTypeSyncEnum {
  /**
   * Event called for checkout tax calculation.
   *
   * Added in Saleor 3.6.
   */
  CheckoutCalculateTaxes = 'CHECKOUT_CALCULATE_TAXES',
  /** Filter shipping methods for checkout. */
  CheckoutFilterShippingMethods = 'CHECKOUT_FILTER_SHIPPING_METHODS',
  /**
   * Event called for order tax calculation.
   *
   * Added in Saleor 3.6.
   */
  OrderCalculateTaxes = 'ORDER_CALCULATE_TAXES',
  /** Filter shipping methods for order. */
  OrderFilterShippingMethods = 'ORDER_FILTER_SHIPPING_METHODS',
  /** Authorize payment. */
  PaymentAuthorize = 'PAYMENT_AUTHORIZE',
  /** Capture payment. */
  PaymentCapture = 'PAYMENT_CAPTURE',
  /** Confirm payment. */
  PaymentConfirm = 'PAYMENT_CONFIRM',
  PaymentGatewayInitializeSession = 'PAYMENT_GATEWAY_INITIALIZE_SESSION',
  /** Listing available payment gateways. */
  PaymentListGateways = 'PAYMENT_LIST_GATEWAYS',
  /** Process payment. */
  PaymentProcess = 'PAYMENT_PROCESS',
  /** Refund payment. */
  PaymentRefund = 'PAYMENT_REFUND',
  /** Void payment. */
  PaymentVoid = 'PAYMENT_VOID',
  /** Fetch external shipping methods for checkout. */
  ShippingListMethodsForCheckout = 'SHIPPING_LIST_METHODS_FOR_CHECKOUT',
  /**
   * Event called when cancel has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionCancelationRequested = 'TRANSACTION_CANCELATION_REQUESTED',
  /**
   * Event called when charge has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionChargeRequested = 'TRANSACTION_CHARGE_REQUESTED',
  TransactionInitializeSession = 'TRANSACTION_INITIALIZE_SESSION',
  TransactionProcessSession = 'TRANSACTION_PROCESS_SESSION',
  /**
   * Event called when refund has been requested for transaction.
   *
   * Added in Saleor 3.13.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  TransactionRefundRequested = 'TRANSACTION_REFUND_REQUESTED'
}

/** An enumeration. */
export enum WebhookSampleEventTypeEnum {
  AddressCreated = 'ADDRESS_CREATED',
  AddressDeleted = 'ADDRESS_DELETED',
  AddressUpdated = 'ADDRESS_UPDATED',
  AppDeleted = 'APP_DELETED',
  AppInstalled = 'APP_INSTALLED',
  AppStatusChanged = 'APP_STATUS_CHANGED',
  AppUpdated = 'APP_UPDATED',
  AttributeCreated = 'ATTRIBUTE_CREATED',
  AttributeDeleted = 'ATTRIBUTE_DELETED',
  AttributeUpdated = 'ATTRIBUTE_UPDATED',
  AttributeValueCreated = 'ATTRIBUTE_VALUE_CREATED',
  AttributeValueDeleted = 'ATTRIBUTE_VALUE_DELETED',
  AttributeValueUpdated = 'ATTRIBUTE_VALUE_UPDATED',
  CategoryCreated = 'CATEGORY_CREATED',
  CategoryDeleted = 'CATEGORY_DELETED',
  CategoryUpdated = 'CATEGORY_UPDATED',
  ChannelCreated = 'CHANNEL_CREATED',
  ChannelDeleted = 'CHANNEL_DELETED',
  ChannelStatusChanged = 'CHANNEL_STATUS_CHANGED',
  ChannelUpdated = 'CHANNEL_UPDATED',
  CheckoutCreated = 'CHECKOUT_CREATED',
  CheckoutFullyPaid = 'CHECKOUT_FULLY_PAID',
  CheckoutMetadataUpdated = 'CHECKOUT_METADATA_UPDATED',
  CheckoutUpdated = 'CHECKOUT_UPDATED',
  CollectionCreated = 'COLLECTION_CREATED',
  CollectionDeleted = 'COLLECTION_DELETED',
  CollectionMetadataUpdated = 'COLLECTION_METADATA_UPDATED',
  CollectionUpdated = 'COLLECTION_UPDATED',
  CustomerCreated = 'CUSTOMER_CREATED',
  CustomerDeleted = 'CUSTOMER_DELETED',
  CustomerMetadataUpdated = 'CUSTOMER_METADATA_UPDATED',
  CustomerUpdated = 'CUSTOMER_UPDATED',
  DraftOrderCreated = 'DRAFT_ORDER_CREATED',
  DraftOrderDeleted = 'DRAFT_ORDER_DELETED',
  DraftOrderUpdated = 'DRAFT_ORDER_UPDATED',
  FulfillmentApproved = 'FULFILLMENT_APPROVED',
  FulfillmentCanceled = 'FULFILLMENT_CANCELED',
  FulfillmentCreated = 'FULFILLMENT_CREATED',
  FulfillmentMetadataUpdated = 'FULFILLMENT_METADATA_UPDATED',
  GiftCardCreated = 'GIFT_CARD_CREATED',
  GiftCardDeleted = 'GIFT_CARD_DELETED',
  GiftCardMetadataUpdated = 'GIFT_CARD_METADATA_UPDATED',
  GiftCardSent = 'GIFT_CARD_SENT',
  GiftCardStatusChanged = 'GIFT_CARD_STATUS_CHANGED',
  GiftCardUpdated = 'GIFT_CARD_UPDATED',
  InvoiceDeleted = 'INVOICE_DELETED',
  InvoiceRequested = 'INVOICE_REQUESTED',
  InvoiceSent = 'INVOICE_SENT',
  MenuCreated = 'MENU_CREATED',
  MenuDeleted = 'MENU_DELETED',
  MenuItemCreated = 'MENU_ITEM_CREATED',
  MenuItemDeleted = 'MENU_ITEM_DELETED',
  MenuItemUpdated = 'MENU_ITEM_UPDATED',
  MenuUpdated = 'MENU_UPDATED',
  NotifyUser = 'NOTIFY_USER',
  Observability = 'OBSERVABILITY',
  OrderCancelled = 'ORDER_CANCELLED',
  OrderConfirmed = 'ORDER_CONFIRMED',
  OrderCreated = 'ORDER_CREATED',
  OrderExpired = 'ORDER_EXPIRED',
  OrderFulfilled = 'ORDER_FULFILLED',
  OrderFullyPaid = 'ORDER_FULLY_PAID',
  OrderFullyRefunded = 'ORDER_FULLY_REFUNDED',
  OrderMetadataUpdated = 'ORDER_METADATA_UPDATED',
  OrderPaid = 'ORDER_PAID',
  OrderRefunded = 'ORDER_REFUNDED',
  OrderUpdated = 'ORDER_UPDATED',
  PageCreated = 'PAGE_CREATED',
  PageDeleted = 'PAGE_DELETED',
  PageTypeCreated = 'PAGE_TYPE_CREATED',
  PageTypeDeleted = 'PAGE_TYPE_DELETED',
  PageTypeUpdated = 'PAGE_TYPE_UPDATED',
  PageUpdated = 'PAGE_UPDATED',
  PermissionGroupCreated = 'PERMISSION_GROUP_CREATED',
  PermissionGroupDeleted = 'PERMISSION_GROUP_DELETED',
  PermissionGroupUpdated = 'PERMISSION_GROUP_UPDATED',
  ProductCreated = 'PRODUCT_CREATED',
  ProductDeleted = 'PRODUCT_DELETED',
  ProductMediaCreated = 'PRODUCT_MEDIA_CREATED',
  ProductMediaDeleted = 'PRODUCT_MEDIA_DELETED',
  ProductMediaUpdated = 'PRODUCT_MEDIA_UPDATED',
  ProductMetadataUpdated = 'PRODUCT_METADATA_UPDATED',
  ProductUpdated = 'PRODUCT_UPDATED',
  ProductVariantBackInStock = 'PRODUCT_VARIANT_BACK_IN_STOCK',
  ProductVariantCreated = 'PRODUCT_VARIANT_CREATED',
  ProductVariantDeleted = 'PRODUCT_VARIANT_DELETED',
  ProductVariantMetadataUpdated = 'PRODUCT_VARIANT_METADATA_UPDATED',
  ProductVariantOutOfStock = 'PRODUCT_VARIANT_OUT_OF_STOCK',
  ProductVariantStockUpdated = 'PRODUCT_VARIANT_STOCK_UPDATED',
  ProductVariantUpdated = 'PRODUCT_VARIANT_UPDATED',
  SaleCreated = 'SALE_CREATED',
  SaleDeleted = 'SALE_DELETED',
  SaleToggle = 'SALE_TOGGLE',
  SaleUpdated = 'SALE_UPDATED',
  ShippingPriceCreated = 'SHIPPING_PRICE_CREATED',
  ShippingPriceDeleted = 'SHIPPING_PRICE_DELETED',
  ShippingPriceUpdated = 'SHIPPING_PRICE_UPDATED',
  ShippingZoneCreated = 'SHIPPING_ZONE_CREATED',
  ShippingZoneDeleted = 'SHIPPING_ZONE_DELETED',
  ShippingZoneMetadataUpdated = 'SHIPPING_ZONE_METADATA_UPDATED',
  ShippingZoneUpdated = 'SHIPPING_ZONE_UPDATED',
  StaffCreated = 'STAFF_CREATED',
  StaffDeleted = 'STAFF_DELETED',
  StaffUpdated = 'STAFF_UPDATED',
  ThumbnailCreated = 'THUMBNAIL_CREATED',
  TransactionActionRequest = 'TRANSACTION_ACTION_REQUEST',
  TransactionItemMetadataUpdated = 'TRANSACTION_ITEM_METADATA_UPDATED',
  TranslationCreated = 'TRANSLATION_CREATED',
  TranslationUpdated = 'TRANSLATION_UPDATED',
  VoucherCreated = 'VOUCHER_CREATED',
  VoucherDeleted = 'VOUCHER_DELETED',
  VoucherMetadataUpdated = 'VOUCHER_METADATA_UPDATED',
  VoucherUpdated = 'VOUCHER_UPDATED',
  WarehouseCreated = 'WAREHOUSE_CREATED',
  WarehouseDeleted = 'WAREHOUSE_DELETED',
  WarehouseMetadataUpdated = 'WAREHOUSE_METADATA_UPDATED',
  WarehouseUpdated = 'WAREHOUSE_UPDATED'
}

/**
 * Trigger a webhook event. Supports a single event (the first, if multiple provided in the `webhook.subscription_query`). Requires permission relevant to processed event. Successfully delivered webhook returns `delivery` with status='PENDING' and empty payload.
 *
 * Added in Saleor 3.11.
 *
 * Note: this API is currently in Feature Preview and can be subject to changes at later point.
 *
 * Requires one of the following permissions: AUTHENTICATED_STAFF_USER.
 */
export type WebhookTrigger = {
  __typename?: 'WebhookTrigger';
  delivery?: Maybe<EventDelivery>;
  errors: Array<WebhookTriggerError>;
};

export type WebhookTriggerError = {
  __typename?: 'WebhookTriggerError';
  /** The error code. */
  code: WebhookTriggerErrorCode;
  /** Name of a field that caused the error. A value of `null` indicates that the error isn't associated with a particular field. */
  field?: Maybe<Scalars['String']['output']>;
  /** The error message. */
  message?: Maybe<Scalars['String']['output']>;
};

/** An enumeration. */
export enum WebhookTriggerErrorCode {
  GraphqlError = 'GRAPHQL_ERROR',
  InvalidId = 'INVALID_ID',
  MissingEvent = 'MISSING_EVENT',
  MissingPermission = 'MISSING_PERMISSION',
  MissingQuery = 'MISSING_QUERY',
  MissingSubscription = 'MISSING_SUBSCRIPTION',
  NotFound = 'NOT_FOUND',
  Syntax = 'SYNTAX',
  TypeNotSupported = 'TYPE_NOT_SUPPORTED',
  UnableToParse = 'UNABLE_TO_PARSE'
}

/**
 * Updates a webhook subscription.
 *
 * Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.
 */
export type WebhookUpdate = {
  __typename?: 'WebhookUpdate';
  errors: Array<WebhookError>;
  webhook?: Maybe<Webhook>;
  /** @deprecated This field will be removed in Saleor 4.0. Use `errors` field instead. */
  webhookErrors: Array<WebhookError>;
};

export type WebhookUpdateInput = {
  /** ID of the app to which webhook belongs. */
  app?: InputMaybe<Scalars['ID']['input']>;
  /** The asynchronous events that webhook wants to subscribe. */
  asyncEvents?: InputMaybe<Array<WebhookEventTypeAsyncEnum>>;
  /**
   * Custom headers, which will be added to HTTP request. There is a limitation of 5 headers per webhook and 998 characters per header.Only "X-*" and "Authorization*" keys are allowed.
   *
   * Added in Saleor 3.12.
   *
   * Note: this API is currently in Feature Preview and can be subject to changes at later point.
   */
  customHeaders?: InputMaybe<Scalars['JSONString']['input']>;
  /**
   * The events that webhook wants to subscribe.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. Use `asyncEvents` or `syncEvents` instead.
   */
  events?: InputMaybe<Array<WebhookEventTypeEnum>>;
  /** Determine if webhook will be set active or not. */
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  /** The new name of the webhook. */
  name?: InputMaybe<Scalars['String']['input']>;
  /**
   * Subscription query used to define a webhook payload.
   *
   * Added in Saleor 3.2.
   */
  query?: InputMaybe<Scalars['String']['input']>;
  /**
   * Use to create a hash signature with each payload.
   *
   * DEPRECATED: this field will be removed in Saleor 4.0. As of Saleor 3.5, webhook payloads default to signing using a verifiable JWS.
   */
  secretKey?: InputMaybe<Scalars['String']['input']>;
  /** The synchronous events that webhook wants to subscribe. */
  syncEvents?: InputMaybe<Array<WebhookEventTypeSyncEnum>>;
  /** The url to receive the payload. */
  targetUrl?: InputMaybe<Scalars['String']['input']>;
};

/** Represents weight value in a specific weight unit. */
export type Weight = {
  __typename?: 'Weight';
  /** Weight unit. */
  unit: WeightUnitsEnum;
  /** Weight value. */
  value: Scalars['Float']['output'];
};

/** An enumeration. */
export enum WeightUnitsEnum {
  G = 'G',
  Kg = 'KG',
  Lb = 'LB',
  Oz = 'OZ',
  Tonne = 'TONNE'
}

/** _Entity union as defined by Federation spec. */
export type _Entity = Address | App | Category | Collection | Group | Order | PageType | Product | ProductMedia | ProductType | ProductVariant | User;

/** _Service manifest as defined by Federation spec. */
export type _Service = {
  __typename?: '_Service';
  sdl?: Maybe<Scalars['String']['output']>;
};

export type TokenCreateMutationVariables = Exact<{
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
}>;


export type TokenCreateMutation = { __typename?: 'Mutation', tokenCreate?: { __typename?: 'CreateToken', csrfToken?: string | null, refreshToken?: string | null, token?: string | null, errors: Array<(
      { __typename?: 'AccountError' }
      & { ' $fragmentRefs'?: { 'AccountErrorFragment': AccountErrorFragment } }
    )>, user?: { __typename?: 'User', id: string, email: string } | null } | null };

export type AccountErrorFragment = { __typename?: 'AccountError', code: AccountErrorCode, field?: string | null, message?: string | null } & { ' $fragmentName'?: 'AccountErrorFragment' };

export const AccountErrorFragmentDoc = {"kind":"Document","definitions":[{"kind":"FragmentDefinition","name":{"kind":"Name","value":"AccountError"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"AccountError"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"code"}},{"kind":"Field","name":{"kind":"Name","value":"field"}},{"kind":"Field","name":{"kind":"Name","value":"message"}}]}}]} as unknown as DocumentNode<AccountErrorFragment, unknown>;
export const TokenCreateDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"TokenCreate"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"email"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"password"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"tokenCreate"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"email"},"value":{"kind":"Variable","name":{"kind":"Name","value":"email"}}},{"kind":"Argument","name":{"kind":"Name","value":"password"},"value":{"kind":"Variable","name":{"kind":"Name","value":"password"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"csrfToken"}},{"kind":"Field","name":{"kind":"Name","value":"refreshToken"}},{"kind":"Field","name":{"kind":"Name","value":"token"}},{"kind":"Field","alias":{"kind":"Name","value":"errors"},"name":{"kind":"Name","value":"accountErrors"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"AccountError"}}]}},{"kind":"Field","name":{"kind":"Name","value":"user"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"email"}}]}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"AccountError"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"AccountError"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"code"}},{"kind":"Field","name":{"kind":"Name","value":"field"}},{"kind":"Field","name":{"kind":"Name","value":"message"}}]}}]} as unknown as DocumentNode<TokenCreateMutation, TokenCreateMutationVariables>;