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
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const SiteSettingsDetails: React.StatelessComponent<
  SiteSettingsDetailsProps
> = ({ data, disabled, onChange }) => (
  <Card>
    <CardTitle
      title={i18n.t("General Information", {
        context: "card title"
      })}
    />
    <CardContent>
      <TextField
        disabled={disabled}
        fullWidth
        name="name"
        label={i18n.t("Store Name", {
          context: "field label"
        })}
        helperText={i18n.t("Store Name is shown on taskbar in web browser", {
          context: "help text"
        })}
        value={data.name}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        fullWidth
        name="domain"
        label={i18n.t("Domain", {
          context: "field label"
        })}
        helperText={i18n.t("Domain is your store URL", {
          context: "help text"
        })}
        value={data.domain}
        onChange={onChange}
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        fullWidth
        name="description"
        label={i18n.t("Store Description", {
          context: "field label"
        })}
        helperText={i18n.t(
          "Store description is shown on taskbar after your store name",
          {
            context: "help text"
          }
        )}
        value={data.description}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
SiteSettingsDetails.displayName = "SiteSettingsDetails";
export default SiteSettingsDetails;
