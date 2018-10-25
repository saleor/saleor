import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { CardSpacer } from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";
import CustomerDetails from "../CustomerDetails/CustomerDetails";
import CustomerOrders from "../CustomerOrders/CustomerOrders";
import CustomerAddresses from "../CustomerAddresses/CustomerAddresses";
import CustomerStats from "../CustomerStats/CustomerStats";

export interface CustomerDetailsPageFormData {
  email: string;
  isActive: boolean;
  note: string;
}

export interface CustomerDetailsPageProps {
  customer: CustomerDetails_user;
  disabled: boolean;
  onBack: () => void;
  onSubmit: (data: CustomerDetails_user) => void;
  onViewAllOrdersClick: () => void;
  onRowClick: (id: string) => void;
  onAddressManageClick: () => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 3 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
const CustomerDetailsPage = decorate<CustomerDetailsPageProps>(
  ({
    classes,
    customer,
    disabled,
    onBack,
    onSubmit,
    onViewAllOrdersClick,
    onRowClick,
    onAddressManageClick
  }) => (
    <Form
      initial={{
        email: maybe(() => customer.email),
        isActive: maybe(() => customer.isActive),
        note: maybe(() => customer.note)
      }}
      key={JSON.stringify(customer)}
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
            onSave={submit}
            onCancel={onBack}
          />
        </Container>
      )}
    </Form>
  )
);
CustomerDetailsPage.displayName = "CustomerDetailsPage";
export default CustomerDetailsPage;
