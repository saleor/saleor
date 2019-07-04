/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PageTranslationDetails
// ====================================================

export interface PageTranslationDetails_page_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface PageTranslationDetails_page_translation {
  __typename: "PageTranslation";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  language: PageTranslationDetails_page_translation_language;
}

export interface PageTranslationDetails_page {
  __typename: "Page";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  translation: PageTranslationDetails_page_translation | null;
}

export interface PageTranslationDetails {
  page: PageTranslationDetails_page | null;
}

export interface PageTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
