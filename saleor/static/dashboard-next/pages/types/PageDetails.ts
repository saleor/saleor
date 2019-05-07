/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PageDetails
// ====================================================

export interface PageDetails_page {
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

export interface PageDetails {
  page: PageDetails_page | null;
}

export interface PageDetailsVariables {
  id: string;
}
