/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { VoucherInput, VoucherDiscountValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VoucherCreate
// ====================================================

export interface VoucherCreate_voucherCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VoucherCreate_voucherCreate_voucher_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface VoucherCreate_voucherCreate_voucher_minAmountSpent {
  __typename: "Money";
  currency: string;
  amount: number;
}

export interface VoucherCreate_voucherCreate_voucher {
  __typename: "Voucher";
  id: string;
  name: string | null;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  discountValueType: VoucherDiscountValueType;
  discountValue: number;
  countries: (VoucherCreate_voucherCreate_voucher_countries | null)[] | null;
  minAmountSpent: VoucherCreate_voucherCreate_voucher_minAmountSpent | null;
}

export interface VoucherCreate_voucherCreate {
  __typename: "VoucherCreate";
  errors: VoucherCreate_voucherCreate_errors[] | null;
  voucher: VoucherCreate_voucherCreate_voucher | null;
}

export interface VoucherCreate {
  voucherCreate: VoucherCreate_voucherCreate | null;
}

export interface VoucherCreateVariables {
  input: VoucherInput;
}
