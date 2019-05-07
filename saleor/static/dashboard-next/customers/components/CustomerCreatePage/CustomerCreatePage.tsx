import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import { CardSpacer } from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import { AddressTypeInput } from "../../types";
import { CustomerCreateData_shop_countries } from "../../types/CustomerCreateData";
import CustomerCreateAddress from "../CustomerCreateAddress/CustomerCreateAddress";
import CustomerCreateDetails from "../CustomerCreateDetails";
import CustomerCreateNote from "../CustomerCreateNote/CustomerCreateNote";

export interface CustomerCreatePageFormData extends AddressTypeInput {
  customerFirstName: string;
  customerLastName: string;
  email: string;
  note: string;
}

const initialForm: CustomerCreatePageFormData = {
  city: "",
  cityArea: "",
  companyName: "",
  country: {
    label: "",
    value: ""
  },
  countryArea: "",
  customerFirstName: "",
  customerLastName: "",
  email: "",
  firstName: "",
  lastName: "",
  note: "",
  phone: "",
  postalCode: "",
  streetAddress1: "",
  streetAddress2: ""
};

export interface CustomerCreatePageProps {
  countries: CustomerCreateData_shop_countries[];
  disabled: boolean;
  errors: UserError[];
  saveButtonBar: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: CustomerCreatePageFormData) => void;
}

const CustomerCreatePage: React.StatelessComponent<CustomerCreatePageProps> = ({
  countries,
  disabled,
  errors,
  saveButtonBar,
  onBack,
  onSubmit
}: CustomerCreatePageProps) => (
  <Form initial={initialForm} onSubmit={onSubmit} errors={errors} confirmLeave>
    {({ change, data, errors: formErrors, hasChanged, submit }) => (
      <Container>
        <AppHeader onBack={onBack}>{i18n.t("Customers")}</AppHeader>
        <PageHeader title={i18n.t("Add customer")} />
        <Grid>
          <div>
            <CustomerCreateDetails
              data={data}
              disabled={disabled}
              errors={formErrors}
              onChange={change}
            />
            <CardSpacer />
            <CustomerCreateAddress
              countries={countries}
              data={data}
              disabled={disabled}
              errors={formErrors}
              onChange={change}
            />
            <CardSpacer />
            <CustomerCreateNote
              data={data}
              disabled={disabled}
              errors={formErrors}
              onChange={change}
            />
          </div>
        </Grid>
        <SaveButtonBar
          disabled={disabled || !hasChanged}
          state={saveButtonBar}
          onSave={submit}
          onCancel={onBack}
        />
      </Container>
    )}
  </Form>
);
CustomerCreatePage.displayName = "CustomerCreatePage";
export default CustomerCreatePage;
