import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";

interface MenuItemPropertiesProps {
  disabled: boolean;
  menuItem: {
    name: string;
    url: string;
  };
  errors: {
    name?: string;
    url?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({ input: { width: "50%" } });
const MenuItemProperties = decorate<MenuItemPropertiesProps>(
  ({ classes, disabled, errors, menuItem, onChange }) => (
    <Card>
      <CardTitle title={i18n.t("General Information")} />
      <CardContent>
        <TextField
          className={classes.input}
          error={!!errors.name}
          helperText={errors.name}
          label={i18n.t("Name")}
          name="name"
          value={menuItem.name}
          disabled={disabled}
          onChange={onChange}
        />
        <FormSpacer />
        <TextField
          error={!!errors.url}
          fullWidth
          helperText={errors.url}
          label={i18n.t("URL (Optional)")}
          name="url"
          value={menuItem.url}
          disabled={disabled}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
MenuItemProperties.displayName = "MenuItemProperties";
export default MenuItemProperties;
