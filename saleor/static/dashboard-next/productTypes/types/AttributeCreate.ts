/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeCreateInput, AttributeTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeCreate
// ====================================================

export interface AttributeCreate_attributeCreate_errors {
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

export interface AttributeCreate_attributeCreate_productType_taxType {
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

export interface AttributeCreate_attributeCreate_productType_productAttributes_values {
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

export interface AttributeCreate_attributeCreate_productType_productAttributes {
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
  values: (AttributeCreate_attributeCreate_productType_productAttributes_values | null)[] | null;
}

export interface AttributeCreate_attributeCreate_productType_variantAttributes_values {
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

export interface AttributeCreate_attributeCreate_productType_variantAttributes {
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
  values: (AttributeCreate_attributeCreate_productType_variantAttributes_values | null)[] | null;
}

export interface AttributeCreate_attributeCreate_productType_weight {
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

export interface AttributeCreate_attributeCreate_productType {
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
  taxType: AttributeCreate_attributeCreate_productType_taxType | null;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (AttributeCreate_attributeCreate_productType_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (AttributeCreate_attributeCreate_productType_variantAttributes | null)[] | null;
  weight: AttributeCreate_attributeCreate_productType_weight | null;
}

export interface AttributeCreate_attributeCreate {
  __typename: "AttributeCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: AttributeCreate_attributeCreate_errors[] | null;
  /**
   * A product type to which an attribute was added.
   */
  productType: AttributeCreate_attributeCreate_productType | null;
}

export interface AttributeCreate {
  /**
   * Creates an attribute.
   */
  attributeCreate: AttributeCreate_attributeCreate | null;
}

export interface AttributeCreateVariables {
  id: string;
  input: AttributeCreateInput;
  type: AttributeTypeEnum;
}
