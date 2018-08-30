import { withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AddressType, OrderStatus, transformAddressToForm } from "../..";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCancelDialog from "../OrderCancelDialog";
import OrderCustomer from "../OrderCustomer";
import OrderCustomerEditDialog from "../OrderCustomerEditDialog";
import OrderFulfillment from "../OrderFulfillment";
import OrderFulfillmentCancelDialog from "../OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog from "../OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../OrderFulfillmentTrackingDialog";
import OrderHistory from "../OrderHistory";
import OrderPaymentDialog from "../OrderPaymentDialog";
import OrderPaymentReleaseDialog from "../OrderPaymentReleaseDialog";
import OrderProductAddDialog from "../OrderProductAddDialog";
import OrderShippingMethodEditDialog from "../OrderShippingMethodEditDialog";
import OrderSummary from "../OrderSummary";

interface TaxedMoneyType {
  gross: {
    amount: number;
    currency: string;
  };
}
interface MoneyType {
  amount: number;
  currency: string;
}
interface OrderDetailsPageProps {
  order?: {
    id: string;
    client: {
      id: string;
      email: string;
      name: string;
    };
    created: string;
    status: string;
    paymentStatus: string;
    shippingAddress?: AddressType;
    billingAddress?: AddressType;
    shippingMethod?: {
      id: string;
    };
    shippingMethodName?: string;
    shippingMethodPriceGross?: MoneyType;
    fulfillments: Array<{
      id: string;
      status: string;
      products: Array<{
        quantity: number;
        product: {
          id: string;
          name: string;
          thumbnailUrl: string;
        };
      }>;
      trackingCode: string;
    }>;
    products?: Array<{
      id: string;
      name: string;
      sku: string;
      thumbnailUrl: string;
      price: TaxedMoneyType;
      quantity: number;
    }>;
    unfulfilled: Array<{
      id: string;
      name: string;
      sku: string;
      thumbnailUrl: string;
      quantity: number;
    }>;
    subtotal: MoneyType;
    total: MoneyType;
    events: Array<{
      id: string;
      type: string;
      content: string;
      date: string;
      user: string;
      params?: {};
    }>;
    payment: {
      paid: MoneyType;
      refunded: MoneyType;
      net: MoneyType;
    };
  };
  shippingMethods?: Array<{
    id: string;
    name: string;
    country: string;
  }>;
  user?: string;
  users?: Array<{
    id: string;
    email: string;
  }>;
  prefixes?: string[];
  countries?: Array<{
    code: string;
    label: string;
  }>;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    stockAllocated;
  }>;
  usersLoading?: boolean;
  variantsLoading?: boolean;
  fetchUsers?(value: string);
  fetchShippingMethods?(value: string);
  fetchVariants?(value: string);
  onBack();
  onCreate?();
  onCustomerEmailClick?(id: string);
  onOrderLineChange?(id: string): (value: string) => () => void;
  onOrderLineRemove?(id: string): () => void;
  onPrintClick?();
  onProductClick?(id: string);
  onPackingSlipClick?(id: string);
  onPaymentRelease?();
  onOrderCancel?();
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
  orderDate: {
    marginBottom: theme.spacing.unit * 2,
    marginLeft: theme.spacing.unit * 10
  },
  root: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
class OrderDetailsPageComponent extends React.Component<
  OrderDetailsPageProps & WithStyles<"orderDate" | "root">,
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
      order,
      prefixes,
      shippingMethods,
      user,
      users,
      variants,
      variantsLoading,
      fetchShippingMethods,
      fetchUsers,
      fetchVariants,
      onBack,
      onCreate,
      onCustomerEmailClick,
      onOrderCancel,
      onOrderLineChange,
      onOrderLineRemove,
      onPackingSlipClick,
      onPaymentRelease,
      onProductClick
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
    const shippingMethod = order
      ? {
          id: order.shippingMethod.id,
          name: order.shippingMethodName,
          price: order.shippingMethodPriceGross
        }
      : undefined;
    return (
      <Container width="md">
        <PageHeader
          title={
            order
              ? i18n.t("Order #{{ orderId }}", { orderId: order.id })
              : undefined
          }
          onBack={onBack}
        />
        {order ? (
          <div className={classes.orderDate}>
            <DateFormatter
              date={order.created}
              typographyProps={{ variant: "caption" }}
            />
          </div>
        ) : (
          <Skeleton />
        )}
        <div className={classes.root}>
          <div>
            <OrderSummary
              net={order ? order.payment.net : undefined}
              paid={order ? order.payment.paid : undefined}
              paymentStatus={order ? order.paymentStatus : undefined}
              products={order ? order.products : undefined}
              refunded={order ? order.payment.refunded : undefined}
              shippingMethod={shippingMethod}
              status={order ? order.status : undefined}
              subtotal={order ? order.subtotal : undefined}
              total={order ? order.total : undefined}
              onCapture={this.togglePaymentCaptureDialog}
              onCreate={onCreate}
              onFulfill={this.toggleFulfillmentDialog}
              onOrderCancel={this.toggleOrderCancelDialog}
              onOrderLineChange={onOrderLineChange}
              onOrderLineRemove={onOrderLineRemove}
              onProductAdd={this.toggleOrderProductAddDialog}
              onRefund={this.togglePaymentRefundDialog}
              onRelease={this.togglePaymentReleaseDialog}
              onRowClick={onProductClick}
              onShippingMethodClick={this.toggleShippingMethodEditDialog}
            />
            {order && (
              <>
                <Form
                  initial={
                    order
                      ? order.unfulfilled.reduce((prev, curr) => {
                          prev[curr.id] = curr.quantity;
                          return prev;
                        }, {})
                      : undefined
                  }
                >
                  {({ data, change, submit }) => (
                    <OrderFulfillmentDialog
                      data={data}
                      open={openedFulfillmentDialog}
                      products={order.unfulfilled}
                      onChange={change}
                      onClose={this.toggleFulfillmentDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
                <Form initial={{ value: 0 }}>
                  {({ data, change, submit }) => (
                    <OrderPaymentDialog
                      open={openedPaymentCaptureDialog}
                      value={data.value}
                      variant="capture"
                      onChange={change}
                      onClose={this.togglePaymentCaptureDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
                <Form initial={{ value: 0 }}>
                  {({ data, change, submit }) => (
                    <OrderPaymentDialog
                      open={openedPaymentRefundDialog}
                      value={data.value}
                      variant="refund"
                      onChange={change}
                      onClose={this.togglePaymentRefundDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
                <Form
                  initial={{
                    quantity: 1,
                    variant: {
                      label: "",
                      value: ""
                    }
                  }}
                >
                  {({ data, change, submit }) => (
                    <OrderProductAddDialog
                      loading={variantsLoading}
                      open={openedOrderProductAddDialog}
                      quantity={data.quantity}
                      variant={data.variant}
                      variants={variants}
                      fetchVariants={fetchVariants}
                      onChange={change}
                      onClose={this.toggleOrderProductAddDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
                <Form
                  initial={{
                    shippingMethod: {
                      label: order.shippingMethodName,
                      value: order.shippingMethod.id
                    }
                  }}
                >
                  {({ change, data }) => (
                    <OrderShippingMethodEditDialog
                      open={openedShippingMethodEditDialog}
                      shippingMethod={data.shippingMethod}
                      shippingMethods={shippingMethods}
                      fetchShippingMethods={fetchShippingMethods}
                      onChange={change}
                      onClose={this.toggleShippingMethodEditDialog}
                    />
                  )}
                </Form>
                <OrderCancelDialog
                  id={order.id}
                  open={openedOrderCancelDialog}
                  onClose={this.toggleOrderCancelDialog}
                  onConfirm={onOrderCancel}
                />
                <OrderPaymentReleaseDialog
                  open={openedPaymentReleaseDialog}
                  onClose={this.togglePaymentReleaseDialog}
                  onConfirm={onPaymentRelease}
                />
              </>
            )}

            {order ? (
              !isDraft &&
              order.fulfillments.map(fulfillment => (
                <Toggle key={fulfillment.id}>
                  {(openedCancelDialog, { toggle: toggleCancelDialog }) => (
                    <Toggle>
                      {(
                        openedTrackingDialog,
                        { toggle: toggleTrackingDialog }
                      ) => (
                        <>
                          <OrderFulfillment
                            id={fulfillment.id}
                            products={fulfillment.products}
                            status={fulfillment.status}
                            trackingCode={fulfillment.trackingCode}
                            onFulfillmentCancel={toggleCancelDialog}
                            onTrackingCodeAdd={toggleTrackingDialog}
                            onPackingSlipClick={
                              onPackingSlipClick
                                ? onPackingSlipClick(fulfillment.id)
                                : undefined
                            }
                          />
                          <OrderFulfillmentCancelDialog
                            open={openedCancelDialog}
                            id={fulfillment.id}
                            onClose={toggleCancelDialog}
                          />
                          <Form
                            initial={{
                              trackingCode: fulfillment.trackingCode
                            }}
                          >
                            {({ change, data }) => (
                              <OrderFulfillmentTrackingDialog
                                open={openedTrackingDialog}
                                trackingCode={data.trackingCode}
                                variant={
                                  fulfillment.trackingCode ? "edit" : "add"
                                }
                                onChange={change}
                                onClose={toggleTrackingDialog}
                              />
                            )}
                          </Form>
                        </>
                      )}
                    </Toggle>
                  )}
                </Toggle>
              ))
            ) : (
              <OrderFulfillment />
            )}
            <OrderHistory
              history={order ? order.events : undefined}
              user={user}
            />
          </div>
          <div>
            <OrderCustomer
              billingAddress={order ? order.billingAddress : undefined}
              client={order ? order.client : undefined}
              editCustomer={isDraft}
              shippingAddress={order ? order.shippingAddress : undefined}
              onBillingAddressEdit={this.toggleBillingAddressEditDialog}
              onCustomerEditClick={this.toggleCustomerEditDialog}
              onCustomerEmailClick={onCustomerEmailClick}
              onShippingAddressEdit={this.toggleShippingAddressEditDialog}
            />
            {order && (
              <>
                <Form
                  initial={{
                    email: order.client
                      ? { label: order.client.email, value: order.client.id }
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
                <Form initial={transformAddressToForm(order.shippingAddress)}>
                  {({ change, data, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      open={openedShippingAddressEditDialog}
                      prefixes={prefixes}
                      variant="shipping"
                      onClose={this.toggleShippingAddressEditDialog}
                      onConfirm={submit}
                      onChange={change}
                    />
                  )}
                </Form>
                <Form initial={transformAddressToForm(order.billingAddress)}>
                  {({ change, data, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      open={openedBillingAddressEditDialog}
                      prefixes={prefixes}
                      variant="billing"
                      onClose={this.toggleBillingAddressEditDialog}
                      onConfirm={submit}
                      onChange={change}
                    />
                  )}
                </Form>
              </>
            )}
          </div>
        </div>
      </Container>
    );
  }
}
const OrderDetailsPage = decorate<OrderDetailsPageProps>(
  OrderDetailsPageComponent
);
export default OrderDetailsPage;
