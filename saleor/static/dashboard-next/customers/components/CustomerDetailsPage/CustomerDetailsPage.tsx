import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AddressType } from "../../";
import ActionDialog from "../../../components/ActionDialog";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import CustomerAddress from "../CustomerAddress/CustomerAddress";
import CustomerDetails from "../CustomerDetails/CustomerDetails";
import CustomerOrders from "../CustomerOrders/CustomerOrders";

interface CustomerDetailsPageProps {
  customer?: {
    id: string;
    dateJoined: string;
    defaultBillingAddress: AddressType;
    defaultShippingAddress: AddressType;
    email: string;
    isActive: boolean;
    isStaff: boolean;
    note: string;
  };
  orders?: Array<{
    id: string;
    number: number;
    created: string;
    price: {
      amount: number;
      currency: string;
    };
    orderStatus: {
      localized: string;
      status: string;
    };
  }>;
  pageInfo?: {
    hasPreviousPage: boolean;
    hasNextPage: boolean;
  };
  onBack?();
  onOrderClick?(id: string): () => void;
  onBillingAddressEdit?();
  onCustomerDelete?();
  onCustomerEdit?();
  onEmailClick?();
  onShippingAddressEdit?();
  onNextPage?();
  onPreviousPage?();
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "2fr 1fr",
    [theme.breakpoints.down("md")]: {
      gridColumnGap: `${theme.spacing.unit}px`
    }
  }
}));
const CustomerDetailsPage = decorate<CustomerDetailsPageProps>(
  ({
    classes,
    customer,
    orders,
    pageInfo,
    onBack,
    onOrderClick,
    onCustomerDelete,
    onCustomerEdit,
    onPreviousPage,
    onNextPage
  }) => (
    <Container width="md">
      <PageHeader
        title={customer ? customer.email : undefined}
        onBack={onBack}
      />
      <Toggle>
        {(isDialogOpened, { toggle: toggleDialog }) => (
          <>
            <div className={classes.root}>
              <div>
                <CustomerDetails
                  customer={customer}
                  onEdit={onCustomerEdit}
                  onDelete={toggleDialog}
                />
                <CustomerOrders
                  hasNextPage={pageInfo ? pageInfo.hasNextPage : undefined}
                  hasPreviousPage={
                    pageInfo ? pageInfo.hasPreviousPage : undefined
                  }
                  orders={orders}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onOrderClick}
                />
              </div>
              <div>
                <CustomerAddress
                  billingAddress={
                    customer ? customer.defaultBillingAddress : undefined
                  }
                  shippingAddress={
                    customer ? customer.defaultShippingAddress : undefined
                  }
                />
              </div>
            </div>

            {customer && (
              <ActionDialog
                open={isDialogOpened}
                title={i18n.t("Delete customer")}
                variant="delete"
                onClose={toggleDialog}
                onConfirm={onCustomerDelete}
              >
                <DialogContentText
                  dangerouslySetInnerHTML={{
                    __html: i18n.t(
                      "Are you sure you want to remove <strong>{{ email }}</strong>?",
                      { email: customer.email }
                    )
                  }}
                />
              </ActionDialog>
            )}
          </>
        )}
      </Toggle>
    </Container>
  )
);
export default CustomerDetailsPage;
