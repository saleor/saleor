import { ApolloClient } from "apollo-client";
import * as React from "react";

import { getAuthToken, removeAuthToken, setAuthToken } from "../../core/auth";
import { UserContext, UserContextInterface } from "./context";
import { tokenVeryficationMutation } from "./queries";
import { TokenAuth_tokenCreate_user } from "./types/TokenAuth";
import { VerifyToken } from "./types/VerifyToken";

export default class UserProvider extends React.Component<
  {
    refreshUser: boolean;
    apolloClient: ApolloClient<any>;
    onUserLogin: () => void;
    onUserLogout: () => void;
    tokenExpirationHandler?(callback: () => void): void;
  },
  UserContextInterface
> {
  constructor(props) {
    super(props);
    if (props.tokenExpirationHandler) {
      props.tokenExpirationHandler(this.logout);
    }
    const token = getAuthToken();
    this.state = {
      authenticate: this.authenticate,
      errors: null,
      loading: !!token,
      login: this.login,
      logout: this.logout,
      token,
      user: null,
    };
  }

  componentDidMount = () => {
    const { token } = this.state;
    if (this.props.refreshUser && token) {
      this.authenticate(token);
    }
  };

  login = (token: string, user: TokenAuth_tokenCreate_user) => {
    this.setState({
      errors: null,
      loading: false,
      token,
      user,
    });
    this.props.onUserLogin();
  };

  logout = () => {
    this.setState({ token: null, user: null });
    this.props.onUserLogout();
  };

  authenticate = async token => {
    this.setState({ loading: true });
    const { apolloClient } = this.props;
    let state = { errors: null, loading: false, token: null, user: null };

    try {
      const {
        data: {
          tokenVerify: { user },
        },
      } = await apolloClient.mutate<VerifyToken>({
        mutation: tokenVeryficationMutation,
        variables: { token },
      });
      state = { ...state, user, token };
    } catch ({ message }) {
      state.errors = message;
    }

    this.setState(state);
  };

  componentDidUpdate = () => {
    if (this.state.token) {
      setAuthToken(this.state.token);
    } else {
      removeAuthToken();
    }
  };

  render() {
    const { children } = this.props;
    return (
      <UserContext.Provider value={this.state}>{children}</UserContext.Provider>
    );
  }
}
