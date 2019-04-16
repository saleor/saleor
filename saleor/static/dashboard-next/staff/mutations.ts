import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { staffMemberDetailsFragment } from "./queries";
import {
  StaffMemberAdd,
  StaffMemberAddVariables
} from "./types/StaffMemberAdd";
import {
  StaffMemberDelete,
  StaffMemberDeleteVariables
} from "./types/StaffMemberDelete";
import {
  StaffMembersBulkDelete,
  StaffMembersBulkDeleteVariables
} from "./types/StaffMembersBulkDelete";
import {
  StaffMemberUpdate,
  StaffMemberUpdateVariables
} from "./types/StaffMemberUpdate";

const staffMemberAddMutation = gql`
  ${staffMemberDetailsFragment}
  mutation StaffMemberAdd($input: StaffCreateInput!) {
    staffCreate(input: $input) {
      errors {
        field
        message
      }
      user {
        ...StaffMemberDetailsFragment
      }
    }
  }
`;
export const TypedStaffMemberAddMutation = TypedMutation<
  StaffMemberAdd,
  StaffMemberAddVariables
>(staffMemberAddMutation);

const staffMemberUpdateMutation = gql`
  ${staffMemberDetailsFragment}
  mutation StaffMemberUpdate($id: ID!, $input: StaffInput!) {
    staffUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      user {
        ...StaffMemberDetailsFragment
      }
    }
  }
`;
export const TypedStaffMemberUpdateMutation = TypedMutation<
  StaffMemberUpdate,
  StaffMemberUpdateVariables
>(staffMemberUpdateMutation);

const staffMemberDeleteMutation = gql`
  mutation StaffMemberDelete($id: ID!) {
    staffDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedStaffMemberDeleteMutation = TypedMutation<
  StaffMemberDelete,
  StaffMemberDeleteVariables
>(staffMemberDeleteMutation);

const staffMembersBulkDeleteMutation = gql`
  mutation StaffMembersBulkDelete($ids: [ID]!) {
    staffBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedStaffMembersBulkDeleteMutation = TypedMutation<
  StaffMembersBulkDelete,
  StaffMembersBulkDeleteVariables
>(staffMembersBulkDeleteMutation);
