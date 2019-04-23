/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageBulkPublish
// ====================================================

export interface PageBulkPublish_pageBulkPublish_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageBulkPublish_pageBulkPublish {
  __typename: "PageBulkPublish";
  errors: PageBulkPublish_pageBulkPublish_errors[] | null;
}

export interface PageBulkPublish {
  pageBulkPublish: PageBulkPublish_pageBulkPublish | null;
}

export interface PageBulkPublishVariables {
  ids: (string | null)[];
  isPublished: boolean;
}
