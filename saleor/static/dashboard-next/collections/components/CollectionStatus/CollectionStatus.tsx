import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { ControlledSwitch } from "../../../components/ControlledSwitch";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";

export interface CollectionStatusProps {
  data: {
    isFeatured: boolean;
    isPublished: boolean;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const CollectionStatus: React.StatelessComponent<CollectionStatusProps> = ({
  data,
  disabled,
  onChange
}) => (
  <Card>
    <CardTitle
      title={i18n.t("Availability", {
        context: "collection status"
      })}
    />
    <CardContent>
      <ControlledSwitch
        checked={data.isPublished}
        disabled={disabled}
        name="isPublished"
        onChange={onChange}
        label={i18n.t("Publish on storefront", {
          context: "button"
        })}
      />
      <FormSpacer />
      <ControlledSwitch
        checked={data.isFeatured}
        disabled={disabled}
        name="isFeatured"
        onChange={onChange}
        label={i18n.t("Feature on Homepage", {
          context: "button"
        })}
      />
    </CardContent>
  </Card>
);
CollectionStatus.displayName = "CollectionStatus";
export default CollectionStatus;
