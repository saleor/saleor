import gql from "graphql-tag";
import { TypedMutation } from "../../core/mutations";
import { ResetPassword, ResetPasswordVariables } from "./types/ResetPassword";

const passwordResetMutation = gql`
  mutation ResetPassword($email: String!) {
    customerPasswordReset(input: { email: $email }) {
      errors {
        field
        message
      }
    }
  }
`;

export const TypedPasswordResetMutation = TypedMutation<
  ResetPassword,
  ResetPasswordVariables
>(passwordResetMutation);
