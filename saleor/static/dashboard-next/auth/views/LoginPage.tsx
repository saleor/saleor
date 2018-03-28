import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import { Redirect } from "react-router-dom";

import Form, { FormProps } from "../../components/Form";
import LoginCard from "../../components/LoginCard";
import { TokenAuthMutationVariables } from "../../gql-types";
import { tokenAuthMutation, TypedTokenAuthMutation } from "../mutations";

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

interface TokenAuthProviderProps {
  children:
    | ((
        authorize: (email: string, password: string) => void
      ) => React.ReactElement<any>)
    | React.ReactNode;
  onAccept(token: string);
}

const TokenAuthProvider: React.StatelessComponent<TokenAuthProviderProps> = ({
  children,
  onAccept
}) => (
  <TypedTokenAuthMutation mutation={tokenAuthMutation}>
    {(mutate, { called, data, error, loading }) => {
      if (called && !loading && !error) {
        const { token } = data.tokenCreate;
        onAccept(token);
        return <Redirect to="/" />;
      }
      if (typeof children === "function") {
        return children((email, password) =>
          mutate({ variables: { email, password } })
        );
      }
      if (React.Children.count(children) > 0) {
        return React.Children.only(children);
      }
      return null;
    }}
  </TypedTokenAuthMutation>
);

const LoginForm: React.ComponentType<
  FormProps<TokenAuthMutationVariables>
> = Form;

interface LoginPageProps {
  onAccept(token: string);
}

const LoginPage = decorate<LoginPageProps>(({ classes, onAccept }) => (
  <TokenAuthProvider onAccept={onAccept}>
    {login => (
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
  </TokenAuthProvider>
));

export default LoginPage;
