import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { SiteSettingsPageFormData } from "../SiteSettingsPage";

interface SiteSettingsDetailsProps {
  data: SiteSettingsPageFormData;
  errors: Partial<{
    description: string;
    domain: string;
    name: string;
  }>;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const SiteSettingsDetails: React.StatelessComponent<
  SiteSettingsDetailsProps
> = ({ data, disabled, errors, onChange }) => (
  <Card>
    <CardTitle
      title={i18n.t("General Information", {
        context: "store configuration"
      })}
    />
    <CardContent>
      <TextField
        disabled={disabled}
        error={!!errors.name}
        fullWidth
        name="name"
        label={i18n.t("Name of your store")}
        helperText={
          errors.name ||
          i18n.t("Name of your store is shown on tab in web browser")
        }
        value={data.name}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.domain}
        fullWidth
        name="domain"
        label={i18n.t("URL of your online store")}
        helperText={errors.domain}
        value={data.domain}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.domain}
        fullWidth
        name="description"
        label={i18n.t("Store Description", {
          context: "field label"
        })}
        helperText={
          errors.description ||
          i18n.t(
            "Store description is shown on taskbar after your store name",
            {
              context: "help text"
            }
          )
        }
        value={data.description}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
SiteSettingsDetails.displayName = "SiteSettingsDetails";
export default SiteSettingsDetails;
