/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PageInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: PageCreate
// ====================================================

export interface PageCreate_pageCreate_errors {
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

export interface PageCreate_pageCreate_page {
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

export interface PageCreate_pageCreate {
  __typename: "PageCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: PageCreate_pageCreate_errors[] | null;
  page: PageCreate_pageCreate_page | null;
}

export interface PageCreate {
  /**
   * Creates a new page.
   */
  pageCreate: PageCreate_pageCreate | null;
}

export interface PageCreateVariables {
  input: PageInput;
}
