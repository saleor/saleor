import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { staffMemberDetailsFragment } from "./queries";
import {
  StaffMemberAdd,
  StaffMemberAddVariables
} from "./types/StaffMemberAdd";

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
