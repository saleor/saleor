import * as React from "react";
import MuiTextField, { TextFieldProps } from "material-ui/TextField";

export const TextField: React.StatelessComponent<TextFieldProps> = props => (
  <MuiTextField
    inputProps={{ className: "browser-default" }}
    fullWidth
    {...props}
  />
);

export default TextField;
