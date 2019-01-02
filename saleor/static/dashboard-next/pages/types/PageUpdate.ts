/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageUpdate
// ====================================================

export interface PageUpdate_pageUpdate_page {
  __typename: "Page";
  id: string;
  slug: string;
  title: string;
  content: string;
  isVisible: boolean;
  availableOn: any | null;
}

export interface PageUpdate_pageUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageUpdate_pageUpdate {
  __typename: "PageUpdate";
  page: PageUpdate_pageUpdate_page | null;
  errors: PageUpdate_pageUpdate_errors[] | null;
}

export interface PageUpdate {
  pageUpdate: PageUpdate_pageUpdate | null;
}

export interface PageUpdateVariables {
  id: string;
  title: string;
  content: string;
  slug: string;
  isVisible: boolean;
  availableOn?: string | null;
}
