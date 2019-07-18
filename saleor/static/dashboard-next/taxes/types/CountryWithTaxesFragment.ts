/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TaxRateType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: CountryWithTaxesFragment
// ====================================================

export interface CountryWithTaxesFragment_vat_reducedRates {
  __typename: "ReducedRate";
  /**
   * A type of goods.
   */
  rateType: TaxRateType;
  /**
   * Reduced VAT rate in percent.
   */
  rate: number;
}

export interface CountryWithTaxesFragment_vat {
  __typename: "VAT";
  /**
   * Standard VAT rate in percent.
   */
  standardRate: number | null;
  /**
   * Country's VAT rate exceptions for specific types of goods.
   */
  reducedRates: (CountryWithTaxesFragment_vat_reducedRates | null)[];
}

export interface CountryWithTaxesFragment {
  __typename: "CountryDisplay";
  /**
   * Country name.
   */
  country: string;
  /**
   * Country code.
   */
  code: string;
  /**
   * Country tax.
   */
  vat: CountryWithTaxesFragment_vat | null;
}
