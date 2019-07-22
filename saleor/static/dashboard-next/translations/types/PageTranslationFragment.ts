/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PageTranslationFragment
// ====================================================

export interface PageTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface PageTranslationFragment_translation {
  __typename: "PageTranslation";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  language: PageTranslationFragment_translation_language;
}

export interface PageTranslationFragment {
  __typename: "Page";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  translation: PageTranslationFragment_translation | null;
}
