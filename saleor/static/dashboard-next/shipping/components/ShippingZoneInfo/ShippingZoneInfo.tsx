import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { FormData } from "../ShippingZoneDetailsPage";

export interface ShippingZoneInfoProps {
  data: FormData;
  errors: FormErrors<"name">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ShippingZoneInfo: React.StatelessComponent<ShippingZoneInfoProps> = ({
  data,
  errors,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
        error={!!errors.name}
        fullWidth
        helperText={errors.name}
        label={i18n.t("Shipping Zone Name")}
        name={"name" as keyof FormData}
        value={data.name}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
ShippingZoneInfo.displayName = "ShippingZoneInfo";
export default ShippingZoneInfo;
