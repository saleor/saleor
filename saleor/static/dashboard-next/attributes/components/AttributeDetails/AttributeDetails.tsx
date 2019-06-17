import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { AttributePageFormData } from "../AttributePage";

export interface AttributeDetailsProps {
  data: AttributePageFormData;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const AttributeDetails: React.FC<AttributeDetailsProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
        disabled={disabled}
        label={i18n.t("Default Label")}
        name={"name" as keyof AttributePageFormData}
        fullWidth
        value={data.name}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        label={i18n.t("Attribute Code")}
        name={"slug" as keyof AttributePageFormData}
        fullWidth
        value={data.slug}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
AttributeDetails.displayName = "AttributeDetails";
export default AttributeDetails;
