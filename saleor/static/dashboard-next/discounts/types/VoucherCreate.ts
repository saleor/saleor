/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { VoucherInput, DiscountValueTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VoucherCreate
// ====================================================

export interface VoucherCreate_voucherCreate_errors {
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

export interface VoucherCreate_voucherCreate_voucher_countries {
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

export interface VoucherCreate_voucherCreate_voucher_minAmountSpent {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
}

export interface VoucherCreate_voucherCreate_voucher {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  code: string;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  /**
   * Determines a type of discount for voucher - value or percentage
   */
  discountValueType: DiscountValueTypeEnum;
  discountValue: number;
  /**
   * List of countries available for the shipping voucher.
   */
  countries: (VoucherCreate_voucherCreate_voucher_countries | null)[] | null;
  minAmountSpent: VoucherCreate_voucherCreate_voucher_minAmountSpent | null;
}

export interface VoucherCreate_voucherCreate {
  __typename: "VoucherCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VoucherCreate_voucherCreate_errors[] | null;
  voucher: VoucherCreate_voucherCreate_voucher | null;
}

export interface VoucherCreate {
  /**
   * Creates a new voucher.
   */
  voucherCreate: VoucherCreate_voucherCreate | null;
}

export interface VoucherCreateVariables {
  input: VoucherInput;
}
