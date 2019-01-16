import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import { CardSpacer } from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
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
  email: "",
  firstName: "",
  lastName: "",
  note: "",
  phone: "",
  postalCode: "",
  streetAddress1: "",
  streetAddress2: ""
};

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 3 + "px",
      gridTemplateColumns: "9fr 4fr"
    }
  });

export interface CustomerCreatePageProps extends WithStyles<typeof styles> {
  countries: CustomerCreateData_shop_countries[];
  disabled: boolean;
  errors: UserError[];
  saveButtonBar: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: CustomerCreatePageFormData) => void;
}

const CustomerCreatePage = withStyles(styles, { name: "CustomerCreatePage" })(
  ({
    classes,
    countries,
    disabled,
    errors,
    saveButtonBar,
    onBack,
    onSubmit
  }: CustomerCreatePageProps) => (
    <Form
      initial={initialForm}
      onSubmit={onSubmit}
      errors={errors}
      confirmLeave
    >
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
          </div>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            state={saveButtonBar}
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
