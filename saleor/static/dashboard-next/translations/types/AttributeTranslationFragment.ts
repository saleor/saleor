/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AttributeTranslationFragment
// ====================================================

export interface AttributeTranslationFragment_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface AttributeTranslationFragment_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface AttributeTranslationFragment_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: AttributeTranslationFragment_values_translation | null;
}

export interface AttributeTranslationFragment {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: AttributeTranslationFragment_translation | null;
  values: (AttributeTranslationFragment_values | null)[] | null;
}
