/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdatePageTranslations
// ====================================================

export interface UpdatePageTranslations_pageTranslate_errors {
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

export interface UpdatePageTranslations_pageTranslate_page_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language code.
   */
  code: LanguageCodeEnum;
  /**
   * Language.
   */
  language: string;
}

export interface UpdatePageTranslations_pageTranslate_page_translation {
  __typename: "PageTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  /**
   * Translation's language
   */
  language: UpdatePageTranslations_pageTranslate_page_translation_language;
}

export interface UpdatePageTranslations_pageTranslate_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  /**
   * Returns translated Page fields for the given language code.
   */
  translation: UpdatePageTranslations_pageTranslate_page_translation | null;
}

export interface UpdatePageTranslations_pageTranslate {
  __typename: "PageTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdatePageTranslations_pageTranslate_errors[] | null;
  page: UpdatePageTranslations_pageTranslate_page | null;
}

export interface UpdatePageTranslations {
  /**
   * Creates/Updates translations for Page.
   */
  pageTranslate: UpdatePageTranslations_pageTranslate | null;
}

export interface UpdatePageTranslationsVariables {
  id: string;
  input: PageTranslationInput;
  language: LanguageCodeEnum;
}
