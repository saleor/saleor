import * as React from "react";

import LoginPage, { FormData } from "../components/LoginPage";
import { UserContext } from "../index";

interface LoginViewProps {
  loading: boolean;
}

const LoginView: React.StatelessComponent<LoginViewProps> = ({ loading }) => (
  <UserContext.Consumer>
    {({ login, user }) => {
      const handleSubmit = (data: FormData) =>
        login(data.email, data.password, data.rememberMe);
      return (
        <LoginPage
          error={user === null}
          disableLoginButton={loading}
          onPasswordRecovery={undefined}
          onSubmit={handleSubmit}
        />
      );
    }}
  </UserContext.Consumer>
);
LoginView.displayName = "LoginView";
export default LoginView;
