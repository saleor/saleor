import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import CardTitle from "../../../components/CardTitle";
import ControlledSwitch from "../../../components/ControlledSwitch";
import Hr from "../../../components/Hr";
import i18n from "../../../i18n";
import { AttributePageFormData } from "../AttributePage";

export interface AttributePropertiesProps {
  data: AttributePageFormData;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const AttributeProperties: React.FC<AttributePropertiesProps> = ({
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("Properties")} />
    <CardContent>
      <Typography variant="subtitle1">
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
      />
    </CardContent>
  </Card>
);
AttributeProperties.displayName = "AttributeProperties";
export default AttributeProperties;
