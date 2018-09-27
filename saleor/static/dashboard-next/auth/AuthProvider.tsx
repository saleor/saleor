import * as React from "react";

import {
  getAuthToken,
  removeAuthToken,
  setAuthToken,
  UserContext
} from "./index";
import { User } from "./types/User";

import TokenAuthProvider from "./containers/TokenAuth";
import TokenVerifyProvider from "./containers/TokenVerify";

interface AuthProviderOperationsProps {
  children:
    | ((
        props: {
          hasToken: boolean;
          isAuthenticated: boolean;
          tokenAuthLoading: boolean;
          tokenVerifyLoading: boolean;
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  onError?: () => void;
}
const AuthProviderOperations: React.StatelessComponent<
  AuthProviderOperationsProps
> = ({ children, onError }) => {
  return (
    <TokenAuthProvider onError={onError}>
      {tokenAuth => (
        <TokenVerifyProvider onError={onError}>
          {tokenVerify => (
            <AuthProvider tokenAuth={tokenAuth} tokenVerify={tokenVerify}>
              {children}
            </AuthProvider>
          )}
        </TokenVerifyProvider>
      )}
    </TokenAuthProvider>
  );
};

interface AuthProviderProps {
  children:
    | ((
        props: {
          hasToken: boolean;
          isAuthenticated: boolean;
          tokenAuthLoading: boolean;
          tokenVerifyLoading: boolean;
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
  tokenAuth: any;
  tokenVerify: any;
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
    if (tokenAuth.error || tokenVerify.error) {
      this.logout();
    }
    if (tokenAuth.data) {
      const user = tokenAuth.data.tokenCreate.user;
      // FIXME: Now we set state also when auth fails and returned user is
      // `null`, because the LoginView uses this `null` to display error.
      this.setState({ user });
      if (user) {
        setAuthToken(tokenAuth.data.tokenCreate.token, this.state.persistToken);
      }
    } else {
      if (tokenVerify.data && tokenVerify.data.tokenVerify.user) {
        const user = tokenVerify.data.tokenVerify.user;
        this.setState({ user });
      }
    }
  }

  componentDidMount() {
    const { user } = this.state;
    const { tokenVerify } = this.props;
    const token = getAuthToken();
    if (!!token && !user) {
      tokenVerify.mutate({ variables: { token } });
    }
  }

  login = (email: string, password: string, persistToken: boolean) => {
    const { tokenAuth } = this.props;
    this.setState({ persistToken });
    tokenAuth.mutate({ variables: { email, password } });
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
        {typeof children === "function"
          ? children({
              hasToken: !!getAuthToken(),
              isAuthenticated,
              tokenAuthLoading: tokenAuth.loading,
              tokenVerifyLoading: tokenVerify.loading
            })
          : children}
      </UserContext.Provider>
    );
  }
}

export default AuthProviderOperations;
