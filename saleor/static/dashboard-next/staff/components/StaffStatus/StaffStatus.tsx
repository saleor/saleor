import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import i18n from "../../../i18n";

interface StaffStatusProps {
  data: {
    isActive: boolean;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const StaffStatus: React.StatelessComponent<StaffStatusProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("Account Status")} />
    <CardContent>
      <Typography>
        {i18n.t("If you want to disable this account uncheck the box below")}
      </Typography>
      <ControlledCheckbox
        checked={data.isActive}
        disabled={disabled}
        label={i18n.t("User is active", { context: "checkbox label" })}
        name="isActive"
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
StaffStatus.displayName = "StaffStatus";
export default StaffStatus;
