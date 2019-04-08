import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { AuthorizationKeyType } from "../../../types/globalTypes";
import { SiteSettings_shop } from "../../types/SiteSettings";
import SiteSettingsDetails from "../SiteSettingsDetails/SiteSettingsDetails";
import SiteSettingsKeys from "../SiteSettingsKeys/SiteSettingsKeys";

export interface SiteSettingsPageFormData {
  description: string;
  domain: string;
  name: string;
}

export interface SiteSettingsPageProps {
  disabled: boolean;
  errors: Array<{
    field: string;
    message: string;
  }>;
  shop: SiteSettings_shop;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onKeyAdd: () => void;
  onKeyRemove: (keyType: AuthorizationKeyType) => void;
  onSubmit: (data: SiteSettingsPageFormData) => void;
}

const SiteSettingsPage: React.StatelessComponent<SiteSettingsPageProps> = ({
  disabled,
  errors,
  saveButtonBarState,
  shop,
  onBack,
  onKeyAdd,
  onKeyRemove,
  onSubmit
}) => {
  const initialForm: SiteSettingsPageFormData = {
    description: maybe(() => shop.description, ""),
    domain: maybe(() => shop.domain.host, ""),
    name: maybe(() => shop.name, "")
  };
  return (
    <Form
      errors={errors}
      initial={initialForm}
      onSubmit={onSubmit}
      confirmLeave
    >
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
          <PageHeader
            title={i18n.t("General Information", {
              context: "page header"
            })}
          />
          <Grid variant="inverted">
            <Typography variant="title">{i18n.t("Site Settings")}</Typography>
            <SiteSettingsDetails
              data={data}
              errors={formErrors}
              disabled={disabled}
              onChange={change}
            />
            <Typography variant="title">
              {i18n.t("Authentication keys")}
            </Typography>
            <SiteSettingsKeys
              disabled={disabled}
              keys={maybe(() => shop.authorizationKeys)}
              onAdd={onKeyAdd}
              onRemove={onKeyRemove}
            />
          </Grid>
          <SaveButtonBar
            state={saveButtonBarState}
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
SiteSettingsPage.displayName = "SiteSettingsPage";
export default SiteSettingsPage;
