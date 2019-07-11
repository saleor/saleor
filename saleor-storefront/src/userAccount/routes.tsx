import React from "react";
import { Route, Switch } from "react-router-dom";

import { NotFound } from "../components";
import { OrderDetails } from "./views";

export const baseUrl = "/my-account/";
export const userOrderDetailsUrl = `${baseUrl}order/:id/`;
export const orderHistoryUrl = `${baseUrl}order/history/`;

const Routes: React.FC = () => (
  <Switch>
    <Route path={userOrderDetailsUrl} component={OrderDetails} />
    <Route component={NotFound} />
  </Switch>
);

export default Routes;
