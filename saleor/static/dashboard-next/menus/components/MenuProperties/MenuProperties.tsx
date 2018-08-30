import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
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

const MenuProperties: React.StatelessComponent<MenuPropertiesProps> = ({
  disabled,
  errors,
  menu,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
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
);
MenuProperties.displayName = "MenuProperties";
export default MenuProperties;
