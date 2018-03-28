import * as React from "react";
import { RouteComponentProps } from "react-router-dom";

import LoginPage from "./views/LoginPage";

const Component: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  return <LoginPage onAccept={setAuthToken} />;
};

export const getAuthToken = () => localStorage.getItem("dashboardAuth");

export const setAuthToken = (token: string) =>
  localStorage.setItem("dashboardAuth", token);

export const removeAuthToken = () => localStorage.removeItem("dashboardAuth");

export default Component;
