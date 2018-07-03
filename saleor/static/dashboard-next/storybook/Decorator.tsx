import CssBaseline from "@material-ui/core/CssBaseline";
import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import * as React from "react";

import { MessageManager } from "../components/messages";
import theme from "../theme";

export const Decorator = storyFn => (
  <MessageManager>
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {storyFn()}
    </MuiThemeProvider>
  </MessageManager>
);
export default Decorator;
