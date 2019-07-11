/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: Price
// ====================================================

export interface Price_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Price {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: Price_gross;
}
