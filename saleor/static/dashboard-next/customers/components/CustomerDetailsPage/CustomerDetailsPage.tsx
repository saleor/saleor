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
import { getUserName, maybe } from "../../../misc";
import { UserError } from "../../../types";
import { CustomerDetails_user } from "../../types/CustomerDetails";
import CustomerAddresses from "../CustomerAddresses/CustomerAddresses";
import CustomerDetails from "../CustomerDetails/CustomerDetails";
import CustomerOrders from "../CustomerOrders/CustomerOrders";
import CustomerStats from "../CustomerStats/CustomerStats";

export interface CustomerDetailsPageFormData {
  firstName: string;
  lastName: string;
  email: string;
  isActive: boolean;
  note: string;
}

export interface CustomerDetailsPageProps {
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

const CustomerDetailsPage: React.StatelessComponent<
  CustomerDetailsPageProps
> = ({
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
      firstName: maybe(() => customer.firstName),
      isActive: maybe(() => customer.isActive, false),
      lastName: maybe(() => customer.lastName),
      note: maybe(() => customer.note)
    }}
    onSubmit={onSubmit}
    confirmLeave
  >
    {({ change, data, errors: formErrors, hasChanged, submit }) => (
      <Container>
        <AppHeader onBack={onBack}>{i18n.t("Customers")}</AppHeader>
        <PageHeader title={getUserName(customer, true)} />
        <Grid>
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
              orders={maybe(() => customer.orders.edges.map(edge => edge.node))}
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
        </Grid>
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
);
CustomerDetailsPage.displayName = "CustomerDetailsPage";
export default CustomerDetailsPage;
