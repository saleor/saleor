import * as React from "react";

import { MutationFn } from "../../../../node_modules/react-apollo";
import {
  TokenAuthMutation,
  TokenAuthMutationVariables,
  UserFragment,
  VerifyTokenMutation,
  VerifyTokenMutationVariables
} from "../gql-types";
import {
  getAuthToken,
  removeAuthToken,
  setAuthToken,
  UserContext
} from "./index";
import {
  tokenAuthMutation,
  tokenVerifyMutation,
  TypedTokenAuthMutation,
  TypedVerifyTokenMutation
} from "./mutations";

interface AuthProviderProps {
  authenticate: MutationFn<TokenAuthMutation, TokenAuthMutationVariables>;
  authResult: any;
  children: any;
  verifyToken: MutationFn<VerifyTokenMutation, VerifyTokenMutationVariables>;
  verifyResult: any;
}

interface AuthProviderState {
  user: UserFragment;
}

class AuthProvider extends React.Component<
  AuthProviderProps,
  AuthProviderState
> {
  constructor(props) {
    super(props);
    this.state = { user: undefined };
  }

  componentWillReceiveProps(props) {
    if (props.authResult.called && !props.authResult.loading) {
      this.setState({ user: props.authResult.data.tokenCreate.user });
      setAuthToken(props.authResult.data.tokenCreate.token);
    }
  }

  componentDidMount() {
    const { user } = this.state;
    const token = getAuthToken();
    if (!!token && !user) {
      this.props
        .verifyToken({ variables: { token } })
        .then(response => {
          if (response) {
            this.setState({ user: response.data.tokenVerify.user });
          }
        })
        .catch(error => {
          this.logout();
        });
    }
  }

  login = (email: string, password: string) => {
    this.props.authenticate({ variables: { email, password } });
  };

  logout = () => {
    this.setState({ user: undefined });
    removeAuthToken();
  };

  setUser = (user: UserFragment) => {
    this.setState({ user });
  };

  render() {
    const { authResult, verifyResult } = this.props;
    const { user } = this.state;
    const isAuthenticated = !!user;
    const loading = authResult.loading || verifyResult.loading;
    return (
      <UserContext.Provider
        value={{ user, login: this.login, logout: this.logout }}
      >
        {loading ? (
          // FIXME: render loading state
          <div>Loading</div>
        ) : (
          this.props.children({ isAuthenticated, logout: this.logout })
        )}
      </UserContext.Provider>
    );
  }
}

const AuthProviderOperations: React.StatelessComponent<any> = ({
  children
}) => (
  <TypedTokenAuthMutation mutation={tokenAuthMutation}>
    {(authenticate, tokenAuthResult) => (
      <TypedVerifyTokenMutation mutation={tokenVerifyMutation}>
        {(verifyToken, verifyTokenResult) => (
          <AuthProvider
            authenticate={authenticate}
            authResult={tokenAuthResult}
            verifyToken={verifyToken}
            verifyResult={verifyTokenResult}
          >
            {({ isAuthenticated }) => {
              return children({ isAuthenticated });
            }}
          </AuthProvider>
        )}
      </TypedVerifyTokenMutation>
    )}
  </TypedTokenAuthMutation>
);

export default AuthProviderOperations;
