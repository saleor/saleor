import "./scss/index.scss";

import * as React from "react";

import { Button, Form, TextField } from "..";
import { maybe } from "../../core/utils";
import { UserContext } from "../User/context";
import { TypedTokenAuthMutation } from "../User/queries";
import { TokenAuth, TokenAuth_tokenCreate_user } from "../User/types/TokenAuth";

interface ILoginForm {
  hide?: () => void;
}

const performLogin = (
  login: (token: string, user: TokenAuth_tokenCreate_user) => void,
  data: TokenAuth,
  hide?: () => void
) => {
  const successful = !data.tokenCreate.errors.length;

  if (successful) {
    if (!!hide) {
      hide();
    }
    login(data.tokenCreate.token, data.tokenCreate.user);
  }
};

const LoginForm: React.FC<ILoginForm> = ({ hide }) => (
  <div className="login-form">
    <UserContext.Consumer>
      {({ login }) => (
        <TypedTokenAuthMutation
          onCompleted={data => performLogin(login, data, hide)}
        >
          {(tokenCreate, { data, loading }) => {
            return (
              <Form
                errors={maybe(() => data.tokenCreate.errors, [])}
                onSubmit={(evt, { email, password }) => {
                  evt.preventDefault();
                  tokenCreate({ variables: { email, password } });
                }}
              >
                <TextField
                  name="email"
                  autoComplete="email"
                  label="Email Address"
                  type="email"
                  required
                />
                <TextField
                  name="password"
                  autoComplete="password"
                  label="Password"
                  type="password"
                  required
                />
                <div className="login-form__button">
                  <Button type="submit" {...loading && { disabled: true }}>
                    {loading ? "Loading" : "Sign in"}
                  </Button>
                </div>
              </Form>
            );
          }}
        </TypedTokenAuthMutation>
      )}
    </UserContext.Consumer>
  </div>
);

export default LoginForm;
