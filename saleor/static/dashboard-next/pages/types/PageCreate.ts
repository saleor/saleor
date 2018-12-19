/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageCreate
// ====================================================

export interface PageCreate_pageCreate_page {
  __typename: "Page";
  id: string;
  slug: string;
  title: string;
  content: string;
  isVisible: boolean;
  availableOn: any | null;
  created: any;
}

export interface PageCreate_pageCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageCreate_pageCreate {
  __typename: "PageCreate";
  page: PageCreate_pageCreate_page | null;
  errors: PageCreate_pageCreate_errors[] | null;
}

export interface PageCreate {
  pageCreate: PageCreate_pageCreate | null;
}

export interface PageCreateVariables {
  title: string;
  content: string;
  slug: string;
  isVisible: boolean;
  availableOn?: string | null;
}
