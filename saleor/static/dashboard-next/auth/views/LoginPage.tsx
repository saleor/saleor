import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Form, { FormProps } from "../../components/Form";
import LoginCard from "../../components/LoginCard";
import { TokenAuthMutationVariables } from "../../gql-types";
import { UserContext } from "../index";

const decorate = withStyles(theme => ({
  root: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.up("sm")]: {
      marginLeft: "auto",
      marginRight: "auto",
      maxWidth: theme.breakpoints.width("sm")
    }
  }
}));

const LoginForm: React.ComponentType<
  FormProps<TokenAuthMutationVariables>
> = Form;

const LoginPage = decorate(({ classes }) => (
  <UserContext.Consumer>
    {({ login }) => (
      <LoginForm
        initial={{ email: "", password: "" }}
        onSubmit={data => login(data.email, data.password)}
      >
        {({ change: handleChange, data, submit: handleSubmit }) => (
          <LoginCard
            className={classes.root}
            errors={[]}
            email={data.email}
            onChange={handleChange}
            onSubmit={handleSubmit}
            password={data.password}
          />
        )}
      </LoginForm>
    )}
  </UserContext.Consumer>
));

export default LoginPage;
