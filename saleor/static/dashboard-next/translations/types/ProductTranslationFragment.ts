/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ProductTranslationFragment
// ====================================================

export interface ProductTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface ProductTranslationFragment_translation {
  __typename: "ProductTranslation";
  id: string;
  descriptionJson: any;
  language: ProductTranslationFragment_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface ProductTranslationFragment {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: ProductTranslationFragment_translation | null;
}
