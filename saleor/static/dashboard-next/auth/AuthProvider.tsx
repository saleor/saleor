import * as React from "react";

import { MutationFn } from "../../../../node_modules/react-apollo";
import {
  UserFragment,
  VerifyTokenMutation,
  VerifyTokenMutationVariables
} from "../gql-types";
import { getAuthToken, removeAuthToken } from "./index";
import { tokenVerifyMutation, TypedVerifyTokenMutation } from "./mutations";

interface AuthProviderProps {
  children: any;
  verifyToken: MutationFn<VerifyTokenMutation, VerifyTokenMutationVariables>;
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

  componentDidMount() {
    const { verifyToken } = this.props;
    const { user } = this.state;
    const token = getAuthToken();
    if (!!token && !user) {
      verifyToken({ variables: { token } })
        .then(response => {
          if (response) {
            this.setState({ user: response.data.tokenVerify.user })
          }
        })
        .catch(error => {
          this.clearUser();
        });
    }
  }

  clearUser = () => {
    this.setState({ user: undefined });
    removeAuthToken();
  };

  setUser = (user: UserFragment) => {
    this.setState({ user });
  };

  render() {
    const { children } = this.props;
    const { user } = this.state;
    const isAuthenticated = !!user;

    if (typeof children === "function") {
      return children({ isAuthenticated, logout: this.clearUser });
    }
    if (React.Children.count(children) > 0) {
      return React.Children.only(children);
    }
    return null;
  }
}

const AuthProviderOperations: React.StatelessComponent<any> = ({
  children,
  logout
}) => (
  <TypedVerifyTokenMutation mutation={tokenVerifyMutation}>
    {(verifyToken, { loading, data, error }) => (
      <AuthProvider verifyToken={verifyToken}>
        {({ isAuthenticated, logout }) => {
          if (loading) {
            // FIXME: "Show more serious loading state here"
            return <div>Loading...</div>
          }
          if (typeof children === "function") {
            return children({ isAuthenticated, logout });
          }
          if (React.Children.count(children) > 0) {
            return React.Children.only(children);
          }
          return null;
        }}
      </AuthProvider>
    )}
  </TypedVerifyTokenMutation>
);

export default AuthProviderOperations;
