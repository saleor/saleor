/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { WeightUnitsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeDetails
// ====================================================

export interface ProductTypeDetails_productType_taxType {
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

export interface ProductTypeDetails_productType_productAttributes_values {
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

export interface ProductTypeDetails_productType_productAttributes {
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
  values: (ProductTypeDetails_productType_productAttributes_values | null)[] | null;
}

export interface ProductTypeDetails_productType_variantAttributes_values {
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

export interface ProductTypeDetails_productType_variantAttributes {
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
  values: (ProductTypeDetails_productType_variantAttributes_values | null)[] | null;
}

export interface ProductTypeDetails_productType_weight {
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

export interface ProductTypeDetails_productType {
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
  taxType: ProductTypeDetails_productType_taxType | null;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductTypeDetails_productType_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (ProductTypeDetails_productType_variantAttributes | null)[] | null;
  weight: ProductTypeDetails_productType_weight | null;
}

export interface ProductTypeDetails_shop {
  __typename: "Shop";
  /**
   * Default weight unit
   */
  defaultWeightUnit: WeightUnitsEnum | null;
}

export interface ProductTypeDetails_taxTypes {
  __typename: "TaxType";
  /**
   * External tax code used to identify given tax group
   */
  taxCode: string | null;
  /**
   * Description of the tax type
   */
  description: string | null;
}

export interface ProductTypeDetails {
  /**
   * Lookup a product type by ID.
   */
  productType: ProductTypeDetails_productType | null;
  /**
   * Represents a shop resources.
   */
  shop: ProductTypeDetails_shop | null;
  /**
   * List of all tax rates available from tax gateway
   */
  taxTypes: (ProductTypeDetails_taxTypes | null)[] | null;
}

export interface ProductTypeDetailsVariables {
  id: string;
}
