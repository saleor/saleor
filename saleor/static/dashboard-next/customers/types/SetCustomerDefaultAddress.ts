/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AddressTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SetCustomerDefaultAddress
// ====================================================

export interface SetCustomerDefaultAddress_addressSetDefault_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_addresses_country {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: SetCustomerDefaultAddress_addressSetDefault_user_addresses_country;
  countryArea: string;
  firstName: string;
  /**
   * The ID of the object.
   */
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_defaultBillingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_defaultShippingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  /**
   * List of all user's addresses.
   */
  addresses: (SetCustomerDefaultAddress_addressSetDefault_user_addresses | null)[] | null;
  defaultBillingAddress: SetCustomerDefaultAddress_addressSetDefault_user_defaultBillingAddress | null;
  defaultShippingAddress: SetCustomerDefaultAddress_addressSetDefault_user_defaultShippingAddress | null;
}

export interface SetCustomerDefaultAddress_addressSetDefault {
  __typename: "AddressSetDefault";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SetCustomerDefaultAddress_addressSetDefault_errors[] | null;
  /**
   * An updated user instance.
   */
  user: SetCustomerDefaultAddress_addressSetDefault_user | null;
}

export interface SetCustomerDefaultAddress {
  /**
   * Sets a default address for the given user.
   */
  addressSetDefault: SetCustomerDefaultAddress_addressSetDefault | null;
}

export interface SetCustomerDefaultAddressVariables {
  addressId: string;
  userId: string;
  type: AddressTypeEnum;
}
