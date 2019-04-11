/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageBulkUnpublish
// ====================================================

export interface PageBulkUnpublish_pageBulkUnpublish_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageBulkUnpublish_pageBulkUnpublish {
  __typename: "PageBulkUnpublish";
  errors: PageBulkUnpublish_pageBulkUnpublish_errors[] | null;
}

export interface PageBulkUnpublish {
  pageBulkUnpublish: PageBulkUnpublish_pageBulkUnpublish | null;
}

export interface PageBulkUnpublishVariables {
  ids: (string | null)[];
}
