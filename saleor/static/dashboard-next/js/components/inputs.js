import React from "react";
import MuiTextField from "material-ui/TextField";

const TextField = props => (
  <MuiTextField
    inputProps={{ className: "browser-default" }}
    fullWidth
    {...props}
  />
);

export { TextField };
