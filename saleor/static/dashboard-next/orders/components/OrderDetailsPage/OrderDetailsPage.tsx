import { withStyles, WithStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { transformAddressToForm } from "../..";
import { UserError } from "../../..";
import { CardMenu } from "../../../components/CardMenu/CardMenu";
import { CardSpacer } from "../../../components/CardSpacer";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import { AddressTypeInput } from "../../../customers";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { OrderStatus } from "../../../types/globalTypes";
import { OrderDetails_order } from "../../types/OrderDetails";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCancelDialog, {
  FormData as OrderCancelFormData
} from "../OrderCancelDialog";
import OrderCustomer from "../OrderCustomer";
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
import OrderUnfulfilledItems from "../OrderUnfulfilledItems/OrderUnfulfilledItems";

export interface OrderDetailsPageProps {
  order: OrderDetails_order;
  shippingMethods?: Array<{
    id: string;
    name: string;
  }>;
  countries?: Array<{
    code: string;
    label: string;
  }>;
  errors: UserError[];
  onBack();
  onBillingAddressEdit(data: AddressTypeInput);
  onFulfillmentCancel(id: string, data: OrderFulfillmentCancelDialogFormData);
  onFulfillmentTrackingNumberUpdate(
    id: string,
    data: OrderFulfillmentTrackingDialogFormData
  );
  onOrderFulfill(data: OrderFulfillFormData);
  onProductClick?(id: string);
  onPaymentCapture(data: OrderPaymentFormData);
  onPaymentRefund(data: OrderPaymentFormData);
  onPaymentRelease?();
  onShippingAddressEdit(data: AddressTypeInput);
  onOrderCancel(data: OrderCancelFormData);
  onNoteAdd(data: HistoryFormData);
}
interface OrderDetailsPageState {
  openedBillingAddressEditDialog: boolean;
  openedFulfillmentDialog: boolean;
  openedOrderCancelDialog: boolean;
  openedPaymentCaptureDialog: boolean;
  openedPaymentRefundDialog: boolean;
  openedPaymentReleaseDialog: boolean;
  openedShippingAddressEditDialog: boolean;
}

const decorate = withStyles(theme => ({
  date: {
    marginBottom: theme.spacing.unit * 3,
    marginLeft: theme.spacing.unit * 7
  },
  header: {
    marginBottom: 0
  },
  menu: {
    marginRight: -theme.spacing.unit
  },
  root: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
class OrderDetailsPageComponent extends React.Component<
  OrderDetailsPageProps & WithStyles<"date" | "header" | "menu" | "root">,
  OrderDetailsPageState
> {
  state = {
    openedBillingAddressEditDialog: false,
    openedFulfillmentDialog: false,
    openedOrderCancelDialog: false,
    openedPaymentCaptureDialog: false,
    openedPaymentRefundDialog: false,
    openedPaymentReleaseDialog: false,
    openedShippingAddressEditDialog: false
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
  toggleShippingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedShippingAddressEditDialog: !prevState.openedShippingAddressEditDialog
    }));
  toggleBillingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedBillingAddressEditDialog: !prevState.openedBillingAddressEditDialog
    }));

  render() {
    const {
      classes,
      countries,
      errors,
      order,
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
      onShippingAddressEdit
    } = this.props;
    const {
      openedBillingAddressEditDialog,
      openedFulfillmentDialog,
      openedOrderCancelDialog,
      openedPaymentCaptureDialog,
      openedPaymentRefundDialog,
      openedPaymentReleaseDialog,
      openedShippingAddressEditDialog
    } = this.state;
    const canCancel = maybe(() => order.status) !== OrderStatus.CANCELED;
    const canEditAddresses = maybe(() => order.status) !== OrderStatus.CANCELED;
    const canFulfill = maybe(() => order.status) !== OrderStatus.CANCELED;
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
          >
            {canCancel && (
              <CardMenu
                className={classes.menu}
                menuItems={[
                  {
                    label: i18n.t("Cancel order", { context: "button" }),
                    onSelect: this.toggleOrderCancelDialog
                  }
                ]}
              />
            )}
          </PageHeader>
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
              {!!maybe(() => order.lines.length > 0) && (
                <OrderUnfulfilledItems
                  canFulfill={canFulfill}
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
                              orderNumber={maybe(() => order.number)}
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
                canEditAddresses={canEditAddresses}
                canEditCustomer={false}
                order={order}
                onBillingAddressEdit={this.toggleBillingAddressEditDialog}
                onShippingAddressEdit={this.toggleShippingAddressEditDialog}
              />
              {order && (
                <>
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
