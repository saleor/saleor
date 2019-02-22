import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";
import { FormData } from "../ShippingZoneDetailsPage";

export interface ShippingZoneInfoProps {
  data: FormData;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ShippingZoneInfo: React.StatelessComponent<ShippingZoneInfoProps> = ({
  data,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
        fullWidth
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
