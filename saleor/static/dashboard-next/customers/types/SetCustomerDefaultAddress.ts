/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AddressTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SetCustomerDefaultAddress
// ====================================================

export interface SetCustomerDefaultAddress_addressSetDefault_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_addresses_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_addresses {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: SetCustomerDefaultAddress_addressSetDefault_user_addresses_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_defaultBillingAddress {
  __typename: "Address";
  id: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user_defaultShippingAddress {
  __typename: "Address";
  id: string;
}

export interface SetCustomerDefaultAddress_addressSetDefault_user {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  addresses: (SetCustomerDefaultAddress_addressSetDefault_user_addresses | null)[] | null;
  defaultBillingAddress: SetCustomerDefaultAddress_addressSetDefault_user_defaultBillingAddress | null;
  defaultShippingAddress: SetCustomerDefaultAddress_addressSetDefault_user_defaultShippingAddress | null;
}

export interface SetCustomerDefaultAddress_addressSetDefault {
  __typename: "AddressSetDefault";
  errors: SetCustomerDefaultAddress_addressSetDefault_errors[] | null;
  user: SetCustomerDefaultAddress_addressSetDefault_user | null;
}

export interface SetCustomerDefaultAddress {
  addressSetDefault: SetCustomerDefaultAddress_addressSetDefault | null;
}

export interface SetCustomerDefaultAddressVariables {
  addressId: string;
  userId: string;
  type: AddressTypeEnum;
}
