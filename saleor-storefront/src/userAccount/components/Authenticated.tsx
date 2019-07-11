import React from "react";

import { NotFound } from "../../components";
import { UserContext } from "../../components/User/context";

const Authenticated: React.FC = ({ children }) => (
  <UserContext.Consumer>
    {({ user }) => (user ? children : <NotFound />)}
  </UserContext.Consumer>
);

export default Authenticated;
