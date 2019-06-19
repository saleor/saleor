import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "@saleor/components/CardTitle";
import FormSpacer from "@saleor/components/FormSpacer";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";
import { AttributePageFormData } from "../AttributePage";

export interface AttributeDetailsProps {
  data: AttributePageFormData;
  disabled: boolean;
  errors: FormErrors<"name" | "slug">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const AttributeDetails: React.FC<AttributeDetailsProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <TextField
        disabled={disabled}
        error={!!errors.name}
        label={i18n.t("Default Label")}
        name={"name" as keyof AttributePageFormData}
        fullWidth
        helperText={errors.name}
        value={data.name}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.slug}
        label={i18n.t("Attribute Code")}
        name={"slug" as keyof AttributePageFormData}
        fullWidth
        helperText={errors.slug}
        value={data.slug}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
AttributeDetails.displayName = "AttributeDetails";
export default AttributeDetails;
