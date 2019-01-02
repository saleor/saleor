import * as React from "react";

import { getMutationProviderData } from "../misc";
import { PartialMutationProviderOutput } from "../types";
import { getAuthToken, removeAuthToken, setAuthToken, UserContext } from "./";
import { TypedTokenAuthMutation, TypedVerifyTokenMutation } from "./mutations";
import { TokenAuth, TokenAuthVariables } from "./types/TokenAuth";
import { User } from "./types/User";
import { VerifyToken, VerifyTokenVariables } from "./types/VerifyToken";

interface AuthProviderOperationsProps {
  children: (
    props: {
      hasToken: boolean;
      isAuthenticated: boolean;
      tokenAuthLoading: boolean;
      tokenVerifyLoading: boolean;
      user: User;
    }
  ) => React.ReactNode;
}
const AuthProviderOperations: React.StatelessComponent<
  AuthProviderOperationsProps
> = ({ children }) => {
  return (
    <TypedTokenAuthMutation>
      {(...tokenAuth) => (
        <TypedVerifyTokenMutation>
          {(...tokenVerify) => (
            <AuthProvider
              tokenAuth={getMutationProviderData(...tokenAuth)}
              tokenVerify={getMutationProviderData(...tokenVerify)}
            >
              {children}
            </AuthProvider>
          )}
        </TypedVerifyTokenMutation>
      )}
    </TypedTokenAuthMutation>
  );
};

interface AuthProviderProps {
  children: (
    props: {
      hasToken: boolean;
      isAuthenticated: boolean;
      tokenAuthLoading: boolean;
      tokenVerifyLoading: boolean;
      user: User;
    }
  ) => React.ReactNode;
  tokenAuth: PartialMutationProviderOutput<TokenAuth, TokenAuthVariables>;
  tokenVerify: PartialMutationProviderOutput<VerifyToken, VerifyTokenVariables>;
}

interface AuthProviderState {
  user: User;
  persistToken: boolean;
}

class AuthProvider extends React.Component<
  AuthProviderProps,
  AuthProviderState
> {
  constructor(props) {
    super(props);
    this.state = { user: undefined, persistToken: false };
  }

  componentWillReceiveProps(props: AuthProviderProps) {
    const { tokenAuth, tokenVerify } = props;
    if (tokenAuth.opts.error || tokenVerify.opts.error) {
      this.logout();
    }
    if (tokenAuth.opts.data) {
      const user = tokenAuth.opts.data.tokenCreate.user;
      // FIXME: Now we set state also when auth fails and returned user is
      // `null`, because the LoginView uses this `null` to display error.
      this.setState({ user });
      if (user) {
        setAuthToken(
          tokenAuth.opts.data.tokenCreate.token,
          this.state.persistToken
        );
      }
    } else {
      if (tokenVerify.opts.data && tokenVerify.opts.data.tokenVerify.user) {
        const user = tokenVerify.opts.data.tokenVerify.user;
        this.setState({ user });
      }
    }
  }

  componentDidMount() {
    const { user } = this.state;
    const { tokenVerify } = this.props;
    const token = getAuthToken();
    if (!!token && !user) {
      tokenVerify.mutate({ token });
    }
  }

  login = (email: string, password: string, persistToken: boolean) => {
    const { tokenAuth } = this.props;
    this.setState({ persistToken });
    tokenAuth.mutate({ email, password });
  };

  logout = () => {
    this.setState({ user: undefined });
    removeAuthToken();
  };

  render() {
    const { children, tokenAuth, tokenVerify } = this.props;
    const { user } = this.state;
    const isAuthenticated = !!user;
    return (
      <UserContext.Provider
        value={{ user, login: this.login, logout: this.logout }}
      >
        {children({
          hasToken: !!getAuthToken(),
          isAuthenticated,
          tokenAuthLoading: tokenAuth.opts.loading,
          tokenVerifyLoading: tokenVerify.opts.loading,
          user
        })}
      </UserContext.Provider>
    );
  }
}

export default AuthProviderOperations;
