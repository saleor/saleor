/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PageDetails
// ====================================================

export interface PageDetails_page {
  __typename: "Page";
  id: string;
  slug: string;
  title: string;
  content: string;
  created: any;
  isPublished: boolean;
  publicationDate: any | null;
}

export interface PageDetails {
  page: PageDetails_page | null;
}

export interface PageDetailsVariables {
  id: string;
}
