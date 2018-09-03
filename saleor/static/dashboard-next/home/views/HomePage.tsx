import * as React from "react";

import { UserContext } from "../../auth";
import { HomeScreen } from "../components/HomeScreen";

const HomePage = () => (
  <UserContext.Consumer>
    {({ user }) => <HomeScreen user={user} />}
  </UserContext.Consumer>
);

export default HomePage;
