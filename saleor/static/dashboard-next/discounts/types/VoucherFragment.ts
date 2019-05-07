/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { VoucherDiscountValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: VoucherFragment
// ====================================================

export interface VoucherFragment_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface VoucherFragment_minAmountSpent {
  __typename: "Money";
  currency: string;
  amount: number;
}

export interface VoucherFragment {
  __typename: "Voucher";
  id: string;
  name: string | null;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  discountValueType: VoucherDiscountValueType;
  discountValue: number;
  countries: (VoucherFragment_countries | null)[] | null;
  minAmountSpent: VoucherFragment_minAmountSpent | null;
}
