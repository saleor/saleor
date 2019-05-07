/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ProductTypeTranslationFragment
// ====================================================

export interface ProductTypeTranslationFragment_productAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationFragment_productAttributes_values_translation | null;
}

export interface ProductTypeTranslationFragment_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationFragment_productAttributes_translation | null;
  values: (ProductTypeTranslationFragment_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationFragment_variantAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationFragment_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationFragment_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslationFragment_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationFragment_variantAttributes_translation | null;
  values: (ProductTypeTranslationFragment_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationFragment {
  __typename: "ProductType";
  id: string;
  name: string;
  productAttributes: (ProductTypeTranslationFragment_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeTranslationFragment_variantAttributes | null)[] | null;
}
