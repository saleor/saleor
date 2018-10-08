import CssBaseline from "@material-ui/core/CssBaseline";
import MuiThemeProvider from "@material-ui/core/styles/MuiThemeProvider";
import * as React from "react";

import { Provider as DateProvider } from "../components/DateFormatter/DateContext";
import { MessageManager } from "../components/messages";
import { TimezoneProvider } from "../components/Timezone";
import theme from "../theme";

export const Decorator = storyFn => (
  <DateProvider value={+new Date("2018-08-07T14:30:44+00:00")}>
    <TimezoneProvider value="America/New_York">
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        <MessageManager>
          <div>{storyFn()}</div>
        </MessageManager>
      </MuiThemeProvider>
    </TimezoneProvider>
  </DateProvider>
);
export default Decorator;
