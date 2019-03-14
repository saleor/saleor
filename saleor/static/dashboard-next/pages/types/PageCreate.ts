/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: PageCreate
// ====================================================

export interface PageCreate_pageCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageCreate_pageCreate_page {
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

export interface PageCreate_pageCreate {
  __typename: "PageCreate";
  errors: PageCreate_pageCreate_errors[] | null;
  page: PageCreate_pageCreate_page | null;
}

export interface PageCreate {
  pageCreate: PageCreate_pageCreate | null;
}

export interface PageCreateVariables {
  input: PageInput;
}
