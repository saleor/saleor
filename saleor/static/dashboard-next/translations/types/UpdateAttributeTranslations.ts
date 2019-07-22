/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateAttributeTranslations
// ====================================================

export interface UpdateAttributeTranslations_attributeTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateAttributeTranslations_attributeTranslate_attribute_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface UpdateAttributeTranslations_attributeTranslate_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: UpdateAttributeTranslations_attributeTranslate_attribute_translation | null;
}

export interface UpdateAttributeTranslations_attributeTranslate {
  __typename: "AttributeTranslate";
  errors: UpdateAttributeTranslations_attributeTranslate_errors[] | null;
  attribute: UpdateAttributeTranslations_attributeTranslate_attribute | null;
}

export interface UpdateAttributeTranslations {
  attributeTranslate: UpdateAttributeTranslations_attributeTranslate | null;
}

export interface UpdateAttributeTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
