import gql from "graphql-tag";

import { TypedMutation } from "@saleor/mutations";
import {
  AttributeBulkDelete,
  AttributeBulkDeleteVariables
} from "./types/AttributeBulkDelete";

const attributeBulkDelete = gql`
  mutation AttributeBulkDelete($ids: [ID!]!) {
    attributeBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const AttributeBulkDeleteMutation = TypedMutation<
  AttributeBulkDelete,
  AttributeBulkDeleteVariables
>(attributeBulkDelete);
