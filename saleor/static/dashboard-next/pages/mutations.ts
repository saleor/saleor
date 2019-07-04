import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { pageDetailsFragment } from "./queries";
import {
  PageBulkPublish,
  PageBulkPublishVariables
} from "./types/PageBulkPublish";
import {
  PageBulkRemove,
  PageBulkRemoveVariables
} from "./types/PageBulkRemove";
import { PageCreate, PageCreateVariables } from "./types/PageCreate";
import { PageRemove, PageRemoveVariables } from "./types/PageRemove";
import { PageUpdate, PageUpdateVariables } from "./types/PageUpdate";

const pageCreate = gql`
  ${pageDetailsFragment}
  mutation PageCreate($input: PageInput!) {
    pageCreate(input: $input) {
      errors {
        field
        message
      }
      page {
        ...PageDetailsFragment
      }
    }
  }
`;
export const TypedPageCreate = TypedMutation<PageCreate, PageCreateVariables>(
  pageCreate
);

const pageUpdate = gql`
  ${pageDetailsFragment}
  mutation PageUpdate($id: ID!, $input: PageInput!) {
    pageUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      page {
        ...PageDetailsFragment
      }
    }
  }
`;
export const TypedPageUpdate = TypedMutation<PageUpdate, PageUpdateVariables>(
  pageUpdate
);

const pageRemove = gql`
  mutation PageRemove($id: ID!) {
    pageDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageRemove = TypedMutation<PageRemove, PageRemoveVariables>(
  pageRemove
);

const pageBulkPublish = gql`
  mutation PageBulkPublish($ids: [ID]!, $isPublished: Boolean!) {
    pageBulkPublish(ids: $ids, isPublished: $isPublished) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageBulkPublish = TypedMutation<
  PageBulkPublish,
  PageBulkPublishVariables
>(pageBulkPublish);

const pageBulkRemove = gql`
  mutation PageBulkRemove($ids: [ID]!) {
    pageBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedPageBulkRemove = TypedMutation<
  PageBulkRemove,
  PageBulkRemoveVariables
>(pageBulkRemove);
