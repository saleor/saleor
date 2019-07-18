/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PageTranslationFragment
// ====================================================

export interface PageTranslationFragment_translation_language {
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

export interface PageTranslationFragment_translation {
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
  language: PageTranslationFragment_translation_language;
}

export interface PageTranslationFragment {
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
  translation: PageTranslationFragment_translation | null;
}
