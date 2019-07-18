/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductTypeDetailsFragment
// ====================================================

export interface ProductTypeDetailsFragment_taxType {
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

export interface ProductTypeDetailsFragment_productAttributes_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface ProductTypeDetailsFragment_productAttributes {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeDetailsFragment_productAttributes_values | null)[] | null;
}

export interface ProductTypeDetailsFragment_variantAttributes_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface ProductTypeDetailsFragment_variantAttributes {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeDetailsFragment_variantAttributes_values | null)[] | null;
}

export interface ProductTypeDetailsFragment_weight {
  __typename: "Weight";
  /**
   * Weight unit
   */
  unit: string;
  /**
   * Weight value
   */
  value: number;
}

export interface ProductTypeDetailsFragment {
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
  taxType: ProductTypeDetailsFragment_taxType | null;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductTypeDetailsFragment_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (ProductTypeDetailsFragment_variantAttributes | null)[] | null;
  weight: ProductTypeDetailsFragment_weight | null;
}
