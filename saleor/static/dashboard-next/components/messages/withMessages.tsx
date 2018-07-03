import * as React from "react";

import { MessageContext } from ".";

export const withMessages = (Component: React.ReactNode) => props => (
  <MessageContext.Consumer>
    {pushMessage => <Component {...props} pushMessage={pushMessage} />}
  </MessageContext.Consumer>
);
