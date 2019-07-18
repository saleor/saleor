/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: PageUpdate
// ====================================================

export interface PageUpdate_pageUpdate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface PageUpdate_pageUpdate_page {
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

export interface PageUpdate_pageUpdate {
  __typename: "PageUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: PageUpdate_pageUpdate_errors[] | null;
  page: PageUpdate_pageUpdate_page | null;
}

export interface PageUpdate {
  /**
   * Updates an existing page.
   */
  pageUpdate: PageUpdate_pageUpdate | null;
}

export interface PageUpdateVariables {
  id: string;
  input: PageInput;
}
