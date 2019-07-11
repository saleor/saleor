import { ApolloError } from "apollo-client";
import * as React from "react";

import { TokenAuth_tokenCreate_user } from "./types/TokenAuth";
import { User } from "./types/User";

export interface UserContextInterface {
  loading: boolean;
  errors: ApolloError[] | null;
  token: string | null;
  user: User | null;
  authenticate(token: string): void;
  logout(): void;
  login(token: string, user: TokenAuth_tokenCreate_user): void;
}

/* tslint:disable:no-empty */
export const UserContext = React.createContext<UserContextInterface>({
  authenticate: token => {},
  errors: null,
  loading: false,
  login: (token, user) => {},
  logout: () => {},
  token: null,
  user: null,
});
/* tslint:enable:no-empty */

UserContext.displayName = "UserContext";
