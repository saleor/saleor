/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateAttributeValueTranslations
// ====================================================

export interface UpdateAttributeValueTranslations_attributeValueTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue_translation | null;
}

export interface UpdateAttributeValueTranslations_attributeValueTranslate {
  __typename: "AttributeValueTranslate";
  errors: UpdateAttributeValueTranslations_attributeValueTranslate_errors[] | null;
  attributeValue: UpdateAttributeValueTranslations_attributeValueTranslate_attributeValue | null;
}

export interface UpdateAttributeValueTranslations {
  attributeValueTranslate: UpdateAttributeValueTranslations_attributeValueTranslate | null;
}

export interface UpdateAttributeValueTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
