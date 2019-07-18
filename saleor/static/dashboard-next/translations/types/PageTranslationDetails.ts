/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PageTranslationDetails
// ====================================================

export interface PageTranslationDetails_page_translation_language {
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

export interface PageTranslationDetails_page_translation {
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
  language: PageTranslationDetails_page_translation_language;
}

export interface PageTranslationDetails_page {
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
  translation: PageTranslationDetails_page_translation | null;
}

export interface PageTranslationDetails {
  /**
   * Lookup a page by ID or by slug.
   */
  page: PageTranslationDetails_page | null;
}

export interface PageTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
