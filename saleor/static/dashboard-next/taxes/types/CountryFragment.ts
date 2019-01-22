/* tslint:disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: CountryFragment
// ====================================================

export interface CountryFragment_vat_reducedRates {
  __typename: "ReducedRate";
  rateType: TaxRateType;
  rate: number;
}

export interface CountryFragment_vat {
  __typename: "VAT";
  standardRate: number | null;
  reducedRates: (CountryFragment_vat_reducedRates | null)[];
}

export interface CountryFragment {
  __typename: "CountryDisplay";
  country: string;
  code: string;
  vat: CountryFragment_vat | null;
}
