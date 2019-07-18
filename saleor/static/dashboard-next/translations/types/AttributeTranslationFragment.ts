/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AttributeTranslationFragment
// ====================================================

export interface AttributeTranslationFragment_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface AttributeTranslationFragment_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface AttributeTranslationFragment_values {
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
  translation: AttributeTranslationFragment_values_translation | null;
}

export interface AttributeTranslationFragment {
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
  translation: AttributeTranslationFragment_translation | null;
  /**
   * List of attribute's values.
   */
  values: (AttributeTranslationFragment_values | null)[] | null;
}
