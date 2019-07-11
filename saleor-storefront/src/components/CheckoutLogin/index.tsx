import "./scss/index.scss";

import React, { useContext, useState } from "react";
import { Redirect } from "react-router";

import { Offline, OfflinePlaceholder, Online, OverlayContext } from "..";

import { baseUrl as checkoutUrl } from "../../checkout/routes";
import { UserContext } from "../User/context";

import CheckoutAsGuest from "./CheckoutAsGuest";
import ResetPasswordForm from "./ResetPasswordForm";
import SignInForm from "./SignInForm";

const CheckoutLogin: React.FC<{}> = () => {
  const [resetPassword, setResetPassword] = useState(false);
  const overlay = useContext(OverlayContext);
  const { user } = useContext(UserContext);
  if (user) {
    return <Redirect to={checkoutUrl} />;
  }
  return (
    <div className="container">
      <Online>
        <div className="checkout-login">
          <CheckoutAsGuest overlay={overlay} checkoutUrl={checkoutUrl} />
          <div className="checkout-login__user">
            {resetPassword ? (
              <ResetPasswordForm
                onClick={() => {
                  setResetPassword(false);
                }}
              />
            ) : (
              <SignInForm
                onClick={() => {
                  setResetPassword(true);
                }}
              />
            )}
          </div>
        </div>
      </Online>
      <Offline>
        <OfflinePlaceholder />
      </Offline>
    </div>
  );
};

export default CheckoutLogin;
