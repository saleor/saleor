/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdatePageTranslations
// ====================================================

export interface UpdatePageTranslations_pageTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdatePageTranslations_pageTranslate_page_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface UpdatePageTranslations_pageTranslate_page_translation {
  __typename: "PageTranslation";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  language: UpdatePageTranslations_pageTranslate_page_translation_language;
}

export interface UpdatePageTranslations_pageTranslate_page {
  __typename: "Page";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  translation: UpdatePageTranslations_pageTranslate_page_translation | null;
}

export interface UpdatePageTranslations_pageTranslate {
  __typename: "PageTranslate";
  errors: UpdatePageTranslations_pageTranslate_errors[] | null;
  page: UpdatePageTranslations_pageTranslate_page | null;
}

export interface UpdatePageTranslations {
  pageTranslate: UpdatePageTranslations_pageTranslate | null;
}

export interface UpdatePageTranslationsVariables {
  id: string;
  input: PageTranslationInput;
  language: LanguageCodeEnum;
}
