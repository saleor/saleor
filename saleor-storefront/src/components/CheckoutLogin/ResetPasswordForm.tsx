import React from "react";
import { PasswordResetForm } from "..";

const ResetPasswordForm: React.FC<{
  onClick: () => void;
}> = ({ onClick }) => (
  <>
    <h3 className="checkout__header">Registered user</h3>
    <PasswordResetForm />
    <p>
      <span className="u-link" onClick={onClick}>
        Back to login
      </span>
    </p>
  </>
);

export default ResetPasswordForm;
