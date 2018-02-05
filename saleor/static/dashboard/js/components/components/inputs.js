import React from 'react';
import MuiTextField from 'material-ui/TextField';
import { withStyles } from 'material-ui/styles';


const TextField = (props) => {
  return (
    <MuiTextField inputProps={{ className: 'browser-default' }}
                  fullWidth
                  {...props} />
  );
};

export {
  TextField,
};
