import * as React from "react";

import LoginCard, { FormData } from "../../components/LoginCard";
import { UserContext } from "../index";

const LoginPage: React.StatelessComponent = () => (
  <UserContext.Consumer>
    {({ login, user }) => {
      const handleSubmit = (data: FormData) =>
        login(data.email, data.password, data.rememberMe);
      return (
        <LoginCard
          error={user === null}
          onPasswordRecovery={() => {}}
          onSubmit={handleSubmit}
        />
      );
    }}
  </UserContext.Consumer>
);

export default LoginPage;
