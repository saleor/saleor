/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductTypeTranslationFragment
// ====================================================

export interface ProductTypeTranslationFragment_productAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_productAttributes_values {
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
   * Returns translated Attribute Value fields for the given language code.
   */
  translation: ProductTypeTranslationFragment_productAttributes_values_translation | null;
}

export interface ProductTypeTranslationFragment_productAttributes {
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
   * Returns translated Attribute fields for the given language code.
   */
  translation: ProductTypeTranslationFragment_productAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslationFragment_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationFragment_variantAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_variantAttributes_values {
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
   * Returns translated Attribute Value fields for the given language code.
   */
  translation: ProductTypeTranslationFragment_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslationFragment_variantAttributes {
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
   * Returns translated Attribute fields for the given language code.
   */
  translation: ProductTypeTranslationFragment_variantAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslationFragment_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationFragment {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductTypeTranslationFragment_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (ProductTypeTranslationFragment_variantAttributes | null)[] | null;
}
