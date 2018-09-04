import * as React from "react";

import LoginPage, { FormData } from "../components/LoginPage";
import { UserContext } from "../index";

const LoginView: React.StatelessComponent = () => (
  <UserContext.Consumer>
    {({ login, user }) => {
      const handleSubmit = (data: FormData) =>
        login(data.email, data.password, data.rememberMe);
      return (
        <LoginPage
          error={user === null}
          onPasswordRecovery={undefined}
          onSubmit={handleSubmit}
        />
      );
    }}
  </UserContext.Consumer>
);

export default LoginView;
