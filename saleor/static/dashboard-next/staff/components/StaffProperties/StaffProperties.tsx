import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ControlledCheckbox from "../../../components/ControlledCheckbox";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface StaffPropertiesProps {
  data: {
    email: string;
    isActive: boolean;
  };
  disabled?: boolean;
  onChange?: (event: React.ChangeEvent<any>) => void;
}

const StaffProperties: React.StatelessComponent<StaffPropertiesProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <PageHeader title={i18n.t("Staff member details")} />
    <CardContent>
      <TextField
        disabled={disabled}
        fullWidth
        label={i18n.t("E-mail")}
        name="email"
        onChange={onChange}
        type="email"
        value={data.email}
      />
      <FormSpacer />
      <ControlledCheckbox
        disabled={disabled}
        checked={data.isActive}
        label={i18n.t("User is active")}
        name="isActive"
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
StaffProperties.displayName = "StaffProperties";
export default StaffProperties;
