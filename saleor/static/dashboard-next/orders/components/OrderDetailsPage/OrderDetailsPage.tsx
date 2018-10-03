import { withStyles, WithStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { transformAddressToForm } from "../..";
import { UserError } from "../../..";
import { CardSpacer } from "../../../components/CardSpacer";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import { AddressTypeInput } from "../../../customers";
import { maybe, renderCollection } from "../../../misc";
import { OrderStatus } from "../../../types/globalTypes";
import { OrderDetails_order } from "../../types/OrderDetails";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCancelDialog, {
  FormData as OrderCancelFormData
} from "../OrderCancelDialog";
import OrderCustomer from "../OrderCustomer";
import OrderCustomerEditDialog from "../OrderCustomerEditDialog";
import OrderFulfillment from "../OrderFulfillment";
import OrderFulfillmentCancelDialog, {
  FormData as OrderFulfillmentCancelDialogFormData
} from "../OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog, {
  FormData as OrderFulfillFormData
} from "../OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog, {
  FormData as OrderFulfillmentTrackingDialogFormData
} from "../OrderFulfillmentTrackingDialog";
import OrderHistory, { FormData as HistoryFormData } from "../OrderHistory";
import OrderPayment from "../OrderPayment/OrderPayment";
import OrderPaymentDialog, {
  FormData as OrderPaymentFormData
} from "../OrderPaymentDialog";
import OrderPaymentReleaseDialog from "../OrderPaymentReleaseDialog";
import OrderProductAddDialog, {
  FormData as ProductAddFormData
} from "../OrderProductAddDialog";
import OrderShippingMethodEditDialog, {
  FormData as ShippingMethodForm
} from "../OrderShippingMethodEditDialog";
import OrderUnfulfilledItems from "../OrderUnfulfilledItems/OrderUnfulfilledItems";

export interface OrderDetailsPageProps {
  order: OrderDetails_order;
  shippingMethods?: Array<{
    id: string;
    name: string;
  }>;
  users?: Array<{
    id: string;
    email: string;
  }>;
  countries?: Array<{
    code: string;
    label: string;
  }>;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    stockQuantity: number;
  }>;
  variantsLoading?: boolean;
  errors: UserError[];
  fetchUsers?(value: string);
  fetchVariants?(value: string);
  onBack();
  onBillingAddressEdit(data: AddressTypeInput);
  onCreate?();
  onFulfillmentCancel(id: string, data: OrderFulfillmentCancelDialogFormData);
  onFulfillmentTrackingNumberUpdate(
    id: string,
    data: OrderFulfillmentTrackingDialogFormData
  );
  onOrderFulfill(data: OrderFulfillFormData);
  onOrderLineChange(id: string): (value: string) => void;
  onOrderLineRemove(id: string);
  onProductAdd(data: ProductAddFormData);
  onProductClick?(id: string);
  onPaymentCapture(data: OrderPaymentFormData);
  onPaymentRefund(data: OrderPaymentFormData);
  onPaymentRelease?();
  onShippingAddressEdit(data: AddressTypeInput);
  onShippingMethodEdit(data: ShippingMethodForm);
  onOrderCancel(data: OrderCancelFormData);
  onNoteAdd(data: HistoryFormData);
}
interface OrderDetailsPageState {
  openedBillingAddressEditDialog: boolean;
  openedCustomerEditDialog: boolean;
  openedFulfillmentDialog: boolean;
  openedOrderCancelDialog: boolean;
  openedOrderProductAddDialog: boolean;
  openedPaymentCaptureDialog: boolean;
  openedPaymentRefundDialog: boolean;
  openedPaymentReleaseDialog: boolean;
  openedShippingAddressEditDialog: boolean;
  openedShippingMethodEditDialog: boolean;
}

const decorate = withStyles(theme => ({
  date: {
    marginBottom: theme.spacing.unit * 3,
    marginLeft: theme.spacing.unit * 7
  },
  header: {
    marginBottom: 0
  },
  root: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
class OrderDetailsPageComponent extends React.Component<
  OrderDetailsPageProps & WithStyles<"date" | "header" | "root">,
  OrderDetailsPageState
> {
  state = {
    openedBillingAddressEditDialog: false,
    openedCustomerEditDialog: false,
    openedFulfillmentDialog: false,
    openedOrderCancelDialog: false,
    openedOrderProductAddDialog: false,
    openedPaymentCaptureDialog: false,
    openedPaymentRefundDialog: false,
    openedPaymentReleaseDialog: false,
    openedShippingAddressEditDialog: false,
    openedShippingMethodEditDialog: false
  };

  toggleFulfillmentDialog = () =>
    this.setState(prevState => ({
      openedFulfillmentDialog: !prevState.openedFulfillmentDialog
    }));
  togglePaymentReleaseDialog = () =>
    this.setState(prevState => ({
      openedPaymentReleaseDialog: !prevState.openedPaymentReleaseDialog
    }));
  togglePaymentCaptureDialog = () =>
    this.setState(prevState => ({
      openedPaymentCaptureDialog: !prevState.openedPaymentCaptureDialog
    }));
  togglePaymentRefundDialog = () =>
    this.setState(prevState => ({
      openedPaymentRefundDialog: !prevState.openedPaymentRefundDialog
    }));
  toggleOrderCancelDialog = () =>
    this.setState(prevState => ({
      openedOrderCancelDialog: !prevState.openedOrderCancelDialog
    }));
  toggleOrderProductAddDialog = () =>
    this.setState(prevState => ({
      openedOrderProductAddDialog: !prevState.openedOrderProductAddDialog
    }));
  toggleCustomerEditDialog = () =>
    this.setState(prevState => ({
      openedCustomerEditDialog: !prevState.openedCustomerEditDialog
    }));
  toggleShippingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedShippingAddressEditDialog: !prevState.openedShippingAddressEditDialog
    }));
  toggleBillingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedBillingAddressEditDialog: !prevState.openedBillingAddressEditDialog
    }));
  toggleShippingMethodEditDialog = () =>
    this.setState(prevState => ({
      openedShippingMethodEditDialog: !prevState.openedShippingMethodEditDialog
    }));

  render() {
    const {
      classes,
      countries,
      errors,
      order,
      shippingMethods,
      users,
      variants,
      variantsLoading,
      fetchUsers,
      fetchVariants,
      onBack,
      onBillingAddressEdit,
      onFulfillmentCancel,
      onFulfillmentTrackingNumberUpdate,
      onNoteAdd,
      onOrderCancel,
      onOrderFulfill,
      onPaymentCapture,
      onPaymentRefund,
      onPaymentRelease,
      onProductAdd,
      onShippingAddressEdit,
      onShippingMethodEdit
    } = this.props;
    const {
      openedBillingAddressEditDialog,
      openedCustomerEditDialog,
      openedFulfillmentDialog,
      openedOrderCancelDialog,
      openedOrderProductAddDialog,
      openedPaymentCaptureDialog,
      openedPaymentRefundDialog,
      openedPaymentReleaseDialog,
      openedShippingAddressEditDialog,
      openedShippingMethodEditDialog
    } = this.state;
    const isDraft = order ? order.status === OrderStatus.DRAFT : false;
    const unfulfilled = maybe(() => order.lines, []).filter(
      line => line.quantityFulfilled < line.quantity
    );
    return (
      <>
        <Container width="md">
          <PageHeader
            className={classes.header}
            title={maybe(() => order.number) ? "#" + order.number : undefined}
            onBack={onBack}
          />
          <div className={classes.date}>
            {order && order.created ? (
              <Typography variant="caption">
                <DateFormatter date={order.created} />
              </Typography>
            ) : (
              <Skeleton style={{ width: "10em" }} />
            )}
          </div>
          <div className={classes.root}>
            <div>
              {!!maybe(() => order.lines.edges.length > 0) && (
                <OrderUnfulfilledItems
                  lines={unfulfilled}
                  onFulfill={this.toggleFulfillmentDialog}
                />
              )}

              {renderCollection(
                maybe(() => order.fulfillments),
                fulfillment => (
                  <Toggle key={maybe(() => fulfillment.id)}>
                    {(
                      openedFulfillmentCancelDialog,
                      { toggle: toggleFulfillmentCancelDialog }
                    ) => (
                      <Toggle>
                        {(
                          openedTrackingDialog,
                          { toggle: toggleTrackingDialog }
                        ) => (
                          <>
                            <CardSpacer />
                            <OrderFulfillment
                              fulfillment={fulfillment}
                              onOrderFulfillmentCancel={
                                toggleFulfillmentCancelDialog
                              }
                              onTrackingCodeAdd={toggleTrackingDialog}
                            />
                            {fulfillment && (
                              <>
                                <OrderFulfillmentCancelDialog
                                  open={openedFulfillmentCancelDialog}
                                  onConfirm={data =>
                                    onFulfillmentCancel(fulfillment.id, data)
                                  }
                                  onClose={toggleFulfillmentCancelDialog}
                                />
                                <OrderFulfillmentTrackingDialog
                                  open={openedTrackingDialog}
                                  trackingNumber={fulfillment.trackingNumber}
                                  onConfirm={data =>
                                    onFulfillmentTrackingNumberUpdate(
                                      fulfillment.id,
                                      data
                                    )
                                  }
                                  onClose={toggleTrackingDialog}
                                />
                              </>
                            )}
                          </>
                        )}
                      </Toggle>
                    )}
                  </Toggle>
                )
              )}

              <CardSpacer />
              <OrderPayment
                order={order}
                onCapture={this.togglePaymentCaptureDialog}
                onRefund={this.togglePaymentRefundDialog}
                onRelease={this.togglePaymentCaptureDialog}
              />

              <OrderHistory
                history={maybe(() => order.events)}
                onNoteAdd={onNoteAdd}
              />
            </div>
            <div>
              <OrderCustomer
                billingAddress={maybe(() => order.billingAddress)}
                customer={maybe(() => order.user)}
                canEditCustomer={isDraft}
                shippingAddress={maybe(() => order.shippingAddress)}
                onBillingAddressEdit={this.toggleBillingAddressEditDialog}
                onCustomerEditClick={this.toggleCustomerEditDialog}
                onShippingAddressEdit={this.toggleShippingAddressEditDialog}
              />
              {order && (
                <>
                  <Form
                    initial={{
                      email: order.user
                        ? { label: order.user.email, value: order.user.id }
                        : { label: "", value: "" }
                    }}
                  >
                    {({ change, data }) => (
                      <OrderCustomerEditDialog
                        open={openedCustomerEditDialog}
                        user={data.email}
                        users={users}
                        fetchUsers={fetchUsers}
                        onChange={change}
                        onClose={this.toggleCustomerEditDialog}
                      />
                    )}
                  </Form>
                  <Form
                    initial={transformAddressToForm(
                      maybe(() => order.shippingAddress)
                    )}
                    errors={errors}
                    onSubmit={onShippingAddressEdit}
                  >
                    {({ change, data, errors: formErrors, submit }) => (
                      <OrderAddressEditDialog
                        countries={countries}
                        data={data}
                        errors={formErrors}
                        open={openedShippingAddressEditDialog}
                        variant="shipping"
                        onChange={change}
                        onClose={this.toggleShippingAddressEditDialog}
                        onConfirm={submit}
                      />
                    )}
                  </Form>
                  <Form
                    initial={transformAddressToForm(order.billingAddress)}
                    errors={errors}
                    onSubmit={onBillingAddressEdit}
                  >
                    {({ change, data, errors: formErrors, submit }) => (
                      <OrderAddressEditDialog
                        countries={countries}
                        data={data}
                        errors={formErrors}
                        open={openedBillingAddressEditDialog}
                        variant="billing"
                        onChange={change}
                        onClose={this.toggleBillingAddressEditDialog}
                        onConfirm={submit}
                      />
                    )}
                  </Form>
                </>
              )}
            </div>
          </div>
        </Container>
        <OrderFulfillmentDialog
          open={openedFulfillmentDialog && !!order}
          lines={unfulfilled}
          onClose={this.toggleFulfillmentDialog}
          onSubmit={onOrderFulfill}
        />
        <OrderPaymentDialog
          open={openedPaymentCaptureDialog && !!order}
          variant="capture"
          onClose={this.togglePaymentCaptureDialog}
          onSubmit={onPaymentCapture}
        />
        <OrderPaymentDialog
          open={openedPaymentRefundDialog && !!order}
          variant="refund"
          onClose={this.togglePaymentRefundDialog}
          onSubmit={onPaymentRefund}
        />
        <OrderProductAddDialog
          loading={variantsLoading}
          open={openedOrderProductAddDialog}
          variants={variants}
          fetchVariants={fetchVariants}
          onClose={this.toggleOrderProductAddDialog}
          onSubmit={onProductAdd}
        />
        <OrderShippingMethodEditDialog
          open={openedShippingMethodEditDialog}
          shippingMethod={maybe(() => order.shippingMethod.id, "")}
          shippingMethods={shippingMethods}
          onClose={this.toggleShippingMethodEditDialog}
          onSubmit={onShippingMethodEdit}
        />
        <OrderCancelDialog
          number={maybe(() => order.number)}
          open={openedOrderCancelDialog}
          onClose={this.toggleOrderCancelDialog}
          onSubmit={onOrderCancel}
        />
        <OrderPaymentReleaseDialog
          open={openedPaymentReleaseDialog}
          onClose={this.togglePaymentReleaseDialog}
          onConfirm={onPaymentRelease}
        />
      </>
    );
  }
}
const OrderDetailsPage = decorate<OrderDetailsPageProps>(
  OrderDetailsPageComponent
);
export default OrderDetailsPage;
