/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateAttributeTranslations
// ====================================================

export interface UpdateAttributeTranslations_attributeTranslate_errors {
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

export interface UpdateAttributeTranslations_attributeTranslate_attribute_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface UpdateAttributeTranslations_attributeTranslate_attribute {
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
  translation: UpdateAttributeTranslations_attributeTranslate_attribute_translation | null;
}

export interface UpdateAttributeTranslations_attributeTranslate {
  __typename: "AttributeTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateAttributeTranslations_attributeTranslate_errors[] | null;
  attribute: UpdateAttributeTranslations_attributeTranslate_attribute | null;
}

export interface UpdateAttributeTranslations {
  /**
   * Creates/Updates translations for Attribute.
   */
  attributeTranslate: UpdateAttributeTranslations_attributeTranslate | null;
}

export interface UpdateAttributeTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
