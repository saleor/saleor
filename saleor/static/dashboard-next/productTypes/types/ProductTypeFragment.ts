/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductTypeFragment
// ====================================================

export interface ProductTypeFragment_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface ProductTypeFragment {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: ProductTypeFragment_taxType | null;
}
