import * as React from "react";
import { RouteComponentProps } from "react-router-dom";

import { UserFragment } from "../gql-types";
import LoginPage from "./views/LoginPage";

interface UserContext {
  login: (username: string, password: string, persist: boolean) => void;
  logout: () => void;
  user?: UserFragment;
}

export const UserContext = React.createContext<UserContext>({
  login: () => {},
  logout: () => {}
});

export const getAuthToken = () =>
  localStorage.getItem("dashboardAuth") ||
  sessionStorage.getItem("dashboardAuth");

export const setAuthToken = (token: string, persist: boolean) =>
  persist
    ? localStorage.setItem("dashboardAuth", token)
    : sessionStorage.setItem("dashboardAuth", token);

export const removeAuthToken = () => {
  localStorage.removeItem("dashboardAuth");
  sessionStorage.removeItem("dashboardAuth");
};

export default LoginPage;
