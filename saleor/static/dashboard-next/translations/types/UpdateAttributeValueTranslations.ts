/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateAttributeValueTranslations
// ====================================================

export interface UpdateAttributeValueTranslations_attributeValueTranslate_errors {
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

export interface UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue {
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
  translation: UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue_translation | null;
}

export interface UpdateAttributeValueTranslations_attributeValueTranslate {
  __typename: "AttributeValueTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateAttributeValueTranslations_attributeValueTranslate_errors[] | null;
  attributeValue: UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue | null;
}

export interface UpdateAttributeValueTranslations {
  /**
   * Creates/Updates translations for Attribute Value.
   */
  attributeValueTranslate: UpdateAttributeValueTranslations_attributeValueTranslate | null;
}

export interface UpdateAttributeValueTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
