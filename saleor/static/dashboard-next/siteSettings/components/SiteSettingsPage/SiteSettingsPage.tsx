import Typography from "@material-ui/core/Typography";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { AuthorizationKeyType } from "../../../types/globalTypes";
import { SiteSettings_shop } from "../../types/SiteSettings";
import SiteSettingsAddress from "../SiteSettingsAddress/SiteSettingsAddress";
import SiteSettingsDetails from "../SiteSettingsDetails/SiteSettingsDetails";
import SiteSettingsKeys from "../SiteSettingsKeys/SiteSettingsKeys";

export interface SiteSettingsPageFormData {
  city: string;
  companyName: string;
  country: {
    code: string;
    country: string;
  };
  countryArea: string;
  description: string;
  domain: string;
  name: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
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
    city: maybe(() => shop.companyAddress.city, ""),
    companyName: maybe(() => shop.companyAddress.companyName, ""),
    country: maybe(() => shop.companyAddress.country, {
      code: "",
      country: ""
    }),
    countryArea: maybe(() => shop.companyAddress.countryArea, ""),
    description: maybe(() => shop.description, ""),
    domain: maybe(() => shop.domain.host, ""),
    name: maybe(() => shop.name, ""),
    phone: maybe(() => shop.companyAddress.phone, ""),
    postalCode: maybe(() => shop.companyAddress.postalCode, ""),
    streetAddress1: maybe(() => shop.companyAddress.streetAddress1, ""),
    streetAddress2: maybe(() => shop.companyAddress.streetAddress2, "")
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
            <Typography variant="h6">{i18n.t("Site Settings")}</Typography>
            <SiteSettingsDetails
              data={data}
              errors={formErrors}
              disabled={disabled}
              onChange={change}
            />
            <Typography variant="h6">
              {i18n.t("Company information")}
            </Typography>
            <SiteSettingsAddress
              data={data}
              countries={maybe(
                () =>
                  shop.countries.map(country => ({
                    code: country.code,
                    label: country.country
                  })),
                []
              )}
              errors={formErrors}
              disabled={disabled}
              onChange={change}
            />
            <Typography variant="h6">
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
