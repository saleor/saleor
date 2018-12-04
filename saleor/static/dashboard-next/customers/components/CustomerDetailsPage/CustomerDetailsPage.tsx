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
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { CustomerDetails_user } from "../../types/CustomerDetails";
import CustomerAddresses from "../CustomerAddresses/CustomerAddresses";
import CustomerDetails from "../CustomerDetails/CustomerDetails";
import CustomerOrders from "../CustomerOrders/CustomerOrders";
import CustomerStats from "../CustomerStats/CustomerStats";

export interface CustomerDetailsPageFormData {
  email: string;
  isActive: boolean;
  note: string;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 3 + "px",
      gridTemplateColumns: "9fr 4fr"
    }
  });

export interface CustomerDetailsPageProps extends WithStyles<typeof styles> {
  customer: CustomerDetails_user;
  disabled: boolean;
  errors: UserError[];
  saveButtonBar: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: CustomerDetailsPageFormData) => void;
  onViewAllOrdersClick: () => void;
  onRowClick: (id: string) => void;
  onAddressManageClick: () => void;
  onDelete: () => void;
}

const CustomerDetailsPage = withStyles(styles, { name: "CustomerDetailsPage" })(
  ({
    classes,
    customer,
    disabled,
    errors,
    saveButtonBar,
    onBack,
    onSubmit,
    onViewAllOrdersClick,
    onRowClick,
    onAddressManageClick,
    onDelete
  }: CustomerDetailsPageProps) => (
    <Form
      errors={errors}
      initial={{
        email: maybe(() => customer.email),
        isActive: maybe(() => customer.isActive),
        note: maybe(() => customer.note)
      }}
      onSubmit={onSubmit}
    >
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader onBack={onBack} title={maybe(() => customer.email)} />
          <div className={classes.root}>
            <div>
              <CustomerDetails
                customer={customer}
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <CustomerOrders
                orders={maybe(() =>
                  customer.orders.edges.map(edge => edge.node)
                )}
                onViewAllOrdersClick={onViewAllOrdersClick}
                onRowClick={onRowClick}
              />
            </div>
            <div>
              <CustomerAddresses
                customer={customer}
                disabled={disabled}
                onAddressManageClick={onAddressManageClick}
              />
              <CardSpacer />
              <CustomerStats customer={customer} />
            </div>
          </div>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            state={saveButtonBar}
            onSave={submit}
            onCancel={onBack}
            onDelete={onDelete}
          />
        </Container>
      )}
    </Form>
  )
);
CustomerDetailsPage.displayName = "CustomerDetailsPage";
export default CustomerDetailsPage;
