import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

interface MenuPropertiesProps {
  disabled: boolean;
  menu: {
    name: string;
  };
  errors: {
    name?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({ input: { width: "50%" } });
const MenuProperties = decorate<MenuPropertiesProps>(
  ({ classes, disabled, errors, menu, onChange }) => (
    <Card>
      <CardTitle title={i18n.t("General Information")} />
      <CardContent>
        <TextField
          className={classes.input}
          error={!!errors.name}
          fullWidth
          helperText={errors.name}
          name="name"
          value={menu.name}
          disabled={disabled}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
MenuProperties.displayName = "MenuProperties";
export default MenuProperties;
