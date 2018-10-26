import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { CardSpacer } from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { AddressTypeInput } from "../../types";
import CustomerCreateAddress from "../CustomerCreateAddress/CustomerCreateAddress";
import CustomerCreateDetails from "../CustomerCreateDetails";
import CustomerCreateNote from "../CustomerCreateNote/CustomerCreateNote";

export interface CustomerCreatePageFormData extends AddressTypeInput {
  email: string;
  note: string;
}

export interface CustomerCreatePageProps {
  disabled: boolean;
  onBack: () => void;
}

const initialForm: CustomerCreatePageFormData = {
  city: "",
  cityArea: "",
  companyName: "",
  country: "",
  countryArea: "",
  email: "",
  firstName: "",
  lastName: "",
  note: "",
  phone: "",
  postalCode: "",
  streetAddress1: "",
  streetAddress2: ""
};

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 3 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
const CustomerCreatePage = decorate<CustomerCreatePageProps>(
  ({ classes, disabled, onBack }) => (
    <Form initial={initialForm}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={i18n.t("Add customer")} onBack={onBack} />
          <div className={classes.root}>
            <div>
              <CustomerCreateDetails
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <CustomerCreateAddress
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
          </div>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onSave={submit}
            onCancel={onBack}
          />
        </Container>
      )}
    </Form>
  )
);
CustomerCreatePage.displayName = "CustomerCreatePage";
export default CustomerCreatePage;
