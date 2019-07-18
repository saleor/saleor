/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductTypeFragment
// ====================================================

export interface ProductTypeFragment_taxType {
  __typename: "TaxType";
  /**
   * Description of the tax type
   */
  description: string | null;
  /**
   * External tax code used to identify given tax group
   */
  taxCode: string | null;
}

export interface ProductTypeFragment {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  /**
   * A type of tax. Assigned by enabled tax gateway
   */
  taxType: ProductTypeFragment_taxType | null;
}
