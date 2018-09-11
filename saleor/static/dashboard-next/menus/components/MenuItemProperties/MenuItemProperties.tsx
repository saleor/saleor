import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { MenuItemLinkedObjectType } from "../..";
import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";

interface MenuItemPropertiesProps {
  cardTitle?: string;
  disabled: boolean;
  menuItem: {
    name: string;
    type: MenuItemLinkedObjectType;
    value: string;
  };
  errors: {
    name?: string;
    value?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({ input: { width: "50%" } });
const MenuItemProperties = decorate<MenuItemPropertiesProps>(
  ({ cardTitle, classes, disabled, errors, menuItem, onChange }) => (
    <Card>
      <CardTitle title={cardTitle || i18n.t("General Information")} />
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
          error={!!errors.value}
          fullWidth
          helperText={errors.value}
          label={i18n.t("URL (Optional)")}
          name="value"
          value={menuItem.value}
          disabled={disabled}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
MenuItemProperties.displayName = "MenuItemProperties";
export default MenuItemProperties;
