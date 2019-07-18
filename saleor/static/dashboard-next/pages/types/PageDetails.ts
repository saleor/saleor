/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PageDetails
// ====================================================

export interface PageDetails_page {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
  slug: string;
  isPublished: boolean;
  contentJson: any;
  seoTitle: string | null;
  seoDescription: string | null;
  publicationDate: any | null;
}

export interface PageDetails {
  /**
   * Lookup a page by ID or by slug.
   */
  page: PageDetails_page | null;
}

export interface PageDetailsVariables {
  id: string;
}
