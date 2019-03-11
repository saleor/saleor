/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: PageUpdate
// ====================================================

export interface PageUpdate_pageUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageUpdate_pageUpdate_page {
  __typename: "Page";
  id: string;
  title: string;
  slug: string;
  isVisible: boolean | null;
  contentJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  availableOn: any | null;
}

export interface PageUpdate_pageUpdate {
  __typename: "PageUpdate";
  errors: PageUpdate_pageUpdate_errors[] | null;
  page: PageUpdate_pageUpdate_page | null;
}

export interface PageUpdate {
  pageUpdate: PageUpdate_pageUpdate | null;
}

export interface PageUpdateVariables {
  id: string;
  input: PageInput;
}
