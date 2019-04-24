import gql from "graphql-tag";
import { TypedMutation } from "../mutations";
import {
  MenuBulkDelete,
  MenuBulkDeleteVariables
} from "./types/MenuBulkDelete";
import { MenuDelete, MenuDeleteVariables } from "./types/MenuDelete";

const menuBulkDelete = gql`
  mutation MenuBulkDelete($ids: [ID]!) {
    menuBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const MenuBulkDeleteMutation = TypedMutation<
  MenuBulkDelete,
  MenuBulkDeleteVariables
>(menuBulkDelete);

const menuDelete = gql`
  mutation MenuDelete($id: ID!) {
    menuDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const MenuDeleteMutation = TypedMutation<
  MenuDelete,
  MenuDeleteVariables
>(menuDelete);
