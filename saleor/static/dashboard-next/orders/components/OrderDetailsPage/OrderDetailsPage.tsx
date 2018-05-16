import PrintIcon from "@material-ui/icons/Print";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import {
  AddressType,
  transformAddressToForm,
  transformOrderStatus
} from "../..";
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
import OrderFulfillment from "../OrderFulfillment";
import OrderFulfillmentCancelDialog from "../OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog from "../OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../OrderFulfillmentTrackingDialog";
import OrderHistory from "../OrderHistory";
import OrderPaymentDialog from "../OrderPaymentDialog";
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
  user?: string;
  prefixes?: string[];
  countries?: Array<{
    code: string;
    label: string;
  }>;
  onBack();
  onCustomerEmailClick?(id: string);
  onPrintClick?();
  onProductClick?(id: string);
  onPackingSlipClick?(id: string);
  onOrderCancel?();
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: "3fr 1fr",
    gridColumnGap: theme.spacing.unit * 2 + "px"
  },
  orderDate: {
    marginLeft: theme.spacing.unit * 10,
    marginBottom: theme.spacing.unit * 2
  }
}));
const OrderDetailsPage = decorate<OrderDetailsPageProps>(
  ({
    classes,
    order,
    user,
    prefixes,
    countries,
    onBack,
    onCustomerEmailClick,
    onPrintClick,
    onProductClick,
    onPackingSlipClick,
    onOrderCancel
  }) => (
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
          <DateFormatter date={order.created} typography="caption" />
        </div>
      ) : (
        <Skeleton />
      )}
      <div className={classes.root}>
        <div>
          <Toggle>
            {(openedFulfillmentDialog, { toggle: toggleFulfillmentDialog }) => (
              <Toggle>
                {(openedPaymentDialog, { toggle: togglePaymentDialog }) => (
                  <Toggle>
                    {(
                      openedPaymentReleaseDialog,
                      { toggle: togglePaymentReleaseDialog }
                    ) => (
                      <Toggle>
                        {(
                          openedPaymentCaptureDialog,
                          { toggle: togglePaymentCaptureDialog }
                        ) => (
                          <Toggle>
                            {(
                              openedPaymentRefundDialog,
                              { toggle: togglePaymentRefundDialog }
                            ) => (
                              <Toggle>
                                {(
                                  openedOrderCancelDialog,
                                  { toggle: toggleOrderCancelDialog }
                                ) => (
                                  <>
                                    <OrderSummary
                                      products={
                                        order ? order.products : undefined
                                      }
                                      subtotal={
                                        order ? order.subtotal : undefined
                                      }
                                      status={order ? order.status : undefined}
                                      paymentStatus={
                                        order ? order.paymentStatus : undefined
                                      }
                                      total={order ? order.total : undefined}
                                      onRowClick={onProductClick}
                                      paid={
                                        order ? order.payment.paid : undefined
                                      }
                                      refunded={
                                        order
                                          ? order.payment.refunded
                                          : undefined
                                      }
                                      net={
                                        order ? order.payment.net : undefined
                                      }
                                      onFulfill={toggleFulfillmentDialog}
                                      onCapture={togglePaymentCaptureDialog}
                                      onRefund={togglePaymentRefundDialog}
                                      onRelease={togglePaymentReleaseDialog}
                                      onOrderCancel={toggleOrderCancelDialog}
                                    />
                                    {order && (
                                      <>
                                        <Form
                                          initial={
                                            order
                                              ? order.unfulfilled.reduce(
                                                  (prev, curr) => {
                                                    prev[curr.id] =
                                                      curr.quantity;
                                                    return prev;
                                                  },
                                                  {}
                                                )
                                              : undefined
                                          }
                                        >
                                          {({ data, change, submit }) => (
                                            <OrderFulfillmentDialog
                                              open={openedFulfillmentDialog}
                                              onClose={toggleFulfillmentDialog}
                                              onChange={change}
                                              products={order.unfulfilled}
                                              onConfirm={submit}
                                              data={data}
                                            />
                                          )}
                                        </Form>
                                        <Form initial={{ value: 0 }}>
                                          {({ data, change, submit }) => (
                                            <OrderPaymentDialog
                                              open={openedPaymentCaptureDialog}
                                              onClose={
                                                togglePaymentCaptureDialog
                                              }
                                              onChange={change}
                                              onConfirm={submit}
                                              value={data.value}
                                              variant="capture"
                                            />
                                          )}
                                        </Form>
                                        <Form initial={{ value: 0 }}>
                                          {({ data, change, submit }) => (
                                            <OrderPaymentDialog
                                              open={openedPaymentRefundDialog}
                                              onClose={
                                                togglePaymentRefundDialog
                                              }
                                              onChange={change}
                                              onConfirm={submit}
                                              value={data.value}
                                              variant="refund"
                                            />
                                          )}
                                        </Form>
                                        <OrderCancelDialog
                                          open={openedOrderCancelDialog}
                                          onClose={toggleOrderCancelDialog}
                                          onConfirm={onOrderCancel}
                                          id={order.id}
                                        />
                                      </>
                                    )}
                                  </>
                                )}
                              </Toggle>
                            )}
                          </Toggle>
                        )}
                      </Toggle>
                    )}
                  </Toggle>
                )}
              </Toggle>
            )}
          </Toggle>
          {order ? (
            order.fulfillments.map(fulfillment => (
              <Toggle>
                {(openedCancelDialog, { toggle: toggleCancelDialog }) => (
                  <Toggle>
                    {(
                      openedTrackingDialog,
                      { toggle: toggleTrackingDialog }
                    ) => (
                      <>
                        <OrderFulfillment
                          products={fulfillment.products}
                          status={fulfillment.status}
                          id={fulfillment.id}
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
                          initial={{ trackingCode: fulfillment.trackingCode }}
                        >
                          {({ change, data, submit }) => (
                            <OrderFulfillmentTrackingDialog
                              open={openedTrackingDialog}
                              onClose={toggleTrackingDialog}
                              onChange={change}
                              trackingCode={data.trackingCode}
                              variant={
                                fulfillment.trackingCode ? "edit" : "add"
                              }
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
          <Toggle>
            {(
              openedShippingAddressEditDialog,
              { toggle: toggleShippingAddressEditDialog }
            ) => (
              <Toggle>
                {(
                  openedBillingAddressEditDialog,
                  { toggle: toggleBillingAddressEditDialog }
                ) => (
                  <>
                    <OrderCustomer
                      client={order ? order.client : undefined}
                      shippingAddress={
                        order ? order.shippingAddress : undefined
                      }
                      billingAddress={order ? order.billingAddress : undefined}
                      onCustomerEmailClick={onCustomerEmailClick}
                      onBillingAddressEdit={toggleBillingAddressEditDialog}
                      onShippingAddressEdit={toggleShippingAddressEditDialog}
                    />
                    {order && (
                      <>
                        <Form
                          initial={transformAddressToForm(
                            order.shippingAddress
                          )}
                        >
                          {({ change, data, submit }) => (
                            <OrderAddressEditDialog
                              variant="shipping"
                              open={openedShippingAddressEditDialog}
                              onClose={toggleShippingAddressEditDialog}
                              onConfirm={submit}
                              onChange={change}
                              prefixes={prefixes}
                              countries={countries}
                              data={data}
                            />
                          )}
                        </Form>
                        <Form
                          initial={transformAddressToForm(order.billingAddress)}
                        >
                          {({ change, data, submit }) => (
                            <OrderAddressEditDialog
                              variant="billing"
                              open={openedBillingAddressEditDialog}
                              onClose={toggleBillingAddressEditDialog}
                              onConfirm={submit}
                              onChange={change}
                              prefixes={prefixes}
                              countries={countries}
                              data={data}
                            />
                          )}
                        </Form>
                      </>
                    )}
                  </>
                )}
              </Toggle>
            )}
          </Toggle>
        </div>
      </div>
    </Container>
  )
);
export default OrderDetailsPage;
