import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor-components/CardTitle";
import i18n from "../../../i18n";
import { MenuDetailsFormData } from "../MenuDetailsPage";

export interface MenuPropertiesProps {
  data: MenuDetailsFormData;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const MenuProperties: React.StatelessComponent<MenuPropertiesProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
        disabled={disabled}
        name={"name" as keyof MenuDetailsFormData}
        fullWidth
        label={i18n.t("Menu Title")}
        value={data.name}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
MenuProperties.displayName = "MenuProperties";
export default MenuProperties;
