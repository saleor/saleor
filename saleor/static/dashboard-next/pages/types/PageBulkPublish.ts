/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageBulkPublish
// ====================================================

export interface PageBulkPublish_pageBulkPublish_errors {
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

export interface PageBulkPublish_pageBulkPublish {
  __typename: "PageBulkPublish";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: PageBulkPublish_pageBulkPublish_errors[] | null;
}

export interface PageBulkPublish {
  /**
   * Publish pages.
   */
  pageBulkPublish: PageBulkPublish_pageBulkPublish | null;
}

export interface PageBulkPublishVariables {
  ids: (string | null)[];
  isPublished: boolean;
}
