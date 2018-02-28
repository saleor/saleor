import React from 'react';
import Reboot from 'material-ui/Reboot';
import { MuiThemeProvider } from 'material-ui/styles';

import theme from '../saleor/static/dashboard/js/components/app/theme';

export default (fn) => (
  <MuiThemeProvider theme={theme}>
    <Reboot />
    <div style={{ padding: 8 }}>
      { fn() }
    </div>
  </MuiThemeProvider>
)
