import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import React from "react";

import CardSpacer from "@saleor/components/CardSpacer";
import CardTitle from "@saleor/components/CardTitle";
import ControlledSwitch from "@saleor/components/ControlledSwitch";
import FormSpacer from "@saleor/components/FormSpacer";
import Hr from "@saleor/components/Hr";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";
import { AttributePageFormData } from "../AttributePage";

export interface AttributePropertiesProps {
  data: AttributePageFormData;
  disabled: boolean;
  errors: FormErrors<"storefrontSearchPosition">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const AttributeProperties: React.FC<AttributePropertiesProps> = ({
  data,
  errors,
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("Properties")} />
    <CardContent>
      {/* <Typography variant="subtitle1">
        {i18n.t("General Properties")}
      </Typography>
      <Hr />
      <CardSpacer />
      <ControlledSwitch
        name={"" as keyof AttributePageFormData}
        checked={false}
        disabled={disabled}
        label={
          <>
            <span>{i18n.t("Variant Attribute")}</span>
            <Typography variant="caption">
              {i18n.t(
                "If enabled, you'll be able to use this attribute to create product variants"
              )}
            </Typography>
          </>
        }
        onChange={onChange}
      /> */}

      <Typography variant="subtitle1">
        {i18n.t("Storefront Properties")}
      </Typography>
      <Hr />
      <ControlledSwitch
        name={"filterableInStorefront" as keyof AttributePageFormData}
        checked={data.filterableInStorefront}
        disabled={disabled}
        label={i18n.t("Use in faceted navigation")}
        onChange={onChange}
      />
      {data.filterableInStorefront && (
        <TextField
          disabled={disabled}
          error={!!errors.storefrontSearchPosition}
          fullWidth
          helperText={errors.storefrontSearchPosition}
          name={"storefrontSearchPosition" as keyof AttributePageFormData}
          label={i18n.t("Position in faceted navigation")}
          value={data.storefrontSearchPosition}
          onChange={onChange}
        />
      )}
      <FormSpacer />
      <ControlledSwitch
        name={"visibleInStorefront" as keyof AttributePageFormData}
        checked={data.visibleInStorefront}
        disabled={disabled}
        label={i18n.t("Visible on Product Page in Storefront", {
          context: "attribute"
        })}
        onChange={onChange}
      />
      <CardSpacer />

      <Typography variant="subtitle1">
        {i18n.t("Dashboard Properties")}
      </Typography>
      <Hr />
      <CardSpacer />
      <ControlledSwitch
        name={"filterableInDashboard" as keyof AttributePageFormData}
        checked={data.filterableInDashboard}
        disabled={disabled}
        label={i18n.t("Use in Filtering")}
        secondLabel={
          <Typography variant="caption">
            {i18n.t(
              "If enabled, you’ll be able to use this attribute to filter products in product list."
            )}
          </Typography>
        }
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
AttributeProperties.displayName = "AttributeProperties";
export default AttributeProperties;
