import * as React from "react";

import Navigator from "./components/Navigator";
import NotFoundPage from "./components/NotFoundPage";

export const NotFound: React.StatelessComponent = () => (
  <Navigator>
    {navigate => <NotFoundPage onBack={() => navigate("/")} />}
  </Navigator>
);
export default NotFound;
