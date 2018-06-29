import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import i18n from "../../../i18n";

interface AttributeDetailsProps {
  data: {
    name: string;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const AttributeDetails: React.StatelessComponent<AttributeDetailsProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <CardContent>
      <TextField
        disabled={disabled}
        fullWidth
        label={i18n.t("Name")}
        name="name"
        value={data.name}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
AttributeDetails.displayName = "AttributeDetails";
export default AttributeDetails;
