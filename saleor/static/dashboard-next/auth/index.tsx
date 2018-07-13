import * as React from "react";
import { RouteComponentProps } from "react-router-dom";

import LoginPage from "./views/LoginPage";

const Component: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  return <LoginPage />;
};

interface UserContext {
  user?: any;
  login?: (username: string, password: string) => void;
  logout?: () => void;
}

export const UserContext = React.createContext<UserContext>({});

export const getAuthToken = () => localStorage.getItem("dashboardAuth");

export const setAuthToken = (token: string) =>
  localStorage.setItem("dashboardAuth", token);

export const removeAuthToken = () => localStorage.removeItem("dashboardAuth");

export default Component;
