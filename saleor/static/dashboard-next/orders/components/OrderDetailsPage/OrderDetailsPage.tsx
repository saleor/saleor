import { withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AddressType, transformAddressToForm } from "../..";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import { Ø } from "../../../misc";
import { OrderEvents, OrderStatus } from "../../../types/globalTypes";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCancelDialog from "../OrderCancelDialog";
import OrderCustomer from "../OrderCustomer";
import OrderCustomerEditDialog from "../OrderCustomerEditDialog";
import OrderFulfillment from "../OrderFulfillment";
import OrderFulfillmentCancelDialog from "../OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog, {
  FormData as OrderFulfillFormData
} from "../OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../OrderFulfillmentTrackingDialog";
import OrderHistory from "../OrderHistory";
import OrderPaymentDialog, {
  FormData as OrderPaymentFormData
} from "../OrderPaymentDialog";
import OrderPaymentReleaseDialog from "../OrderPaymentReleaseDialog";
import OrderProductAddDialog, {
  FormData as ProductAddFormData
} from "../OrderProductAddDialog";
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
    billingAddress?: AddressType;
    created: string;
    fulfillments: Array<{
      id: string;
      lines: {
        edges: Array<{
          node: {
            quantity: number;
            orderLine: {
              id: string;
              productName: string;
              thumbnailUrl?: string;
            };
          };
        }>;
      };
      status: string;
      trackingNumber: string;
    }>;
    events: Array<{
      amount?: number;
      date: string;
      email?: string;
      emailType?: string;
      id: string;
      message?: string;
      quantity?: number;
      type: OrderEvents;
      user: {
        email: string;
      };
    }>;
    lines: {
      edges: Array<{
        node: {
          id: string;
          productName: string;
          productSku: string;
          thumbnailUrl?: string;
          unitPrice: TaxedMoneyType;
          quantity: number;
          quantityFulfilled: number;
        };
      }>;
    };
    number: string;
    paymentStatus: string;
    shippingAddress?: AddressType;
    shippingMethod?: {
      id: string;
    };
    shippingMethodName?: string;
    shippingPrice?: {
      gross: MoneyType;
    };
    status: OrderStatus;
    subtotal: {
      gross: MoneyType;
    };
    total: {
      gross: MoneyType;
      tax: MoneyType;
    };
    totalAuthorized: MoneyType;
    totalCaptured: MoneyType;
    user: {
      id: string;
      email: string;
    };
  };
  shippingMethods?: Array<{
    id: string;
    name: string;
  }>;
  user?: {
    email: string;
  };
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
  fetchUsers?(value: string);
  fetchShippingMethods?(value: string);
  fetchVariants?(value: string);
  onBack();
  onCreate?();
  onCustomerEmailClick?(id: string);
  onOrderFulfill(data: OrderFulfillFormData);
  onOrderLineChange?(id: string): (value: string) => () => void;
  onOrderLineRemove?(id: string): () => void;
  onProductAdd(data: ProductAddFormData);
  onProductClick?(id: string);
  onPackingSlipClick?(id: string);
  onPaymentCapture(data: OrderPaymentFormData);
  onPaymentRefund(data: OrderPaymentFormData);
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
      onOrderFulfill,
      onOrderLineChange,
      onOrderLineRemove,
      onPackingSlipClick,
      onPaymentCapture,
      onPaymentRefund,
      onPaymentRelease,
      onProductAdd,
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
    const unfulfilled = Ø(() => order.lines.edges, [])
      .map(edge => edge.node)
      .filter(line => line.quantityFulfilled < line.quantity);
    return (
      <Container width="md">
        <PageHeader
          title={
            order
              ? i18n.t("Order #{{ orderId }}", { orderId: order.number })
              : undefined
          }
          onBack={onBack}
        />
        {order ? (
          <div className={classes.orderDate}>
            {order && order.created ? (
              <DateFormatter
                date={order.created}
                typographyProps={{ variant: "caption" }}
              />
            ) : (
              <Skeleton />
            )}
          </div>
        ) : (
          <Skeleton />
        )}
        <div className={classes.root}>
          <div>
            <OrderSummary
              authorized={Ø(() => order.totalAuthorized)}
              paid={Ø(() => order.totalCaptured)}
              paymentStatus={Ø(() => order.paymentStatus)}
              lines={Ø(() => order.lines.edges.map(edge => edge.node))}
              shippingMethodName={Ø(() => order.shippingMethodName)}
              shippingPrice={Ø(() => order.shippingPrice)}
              status={Ø(() => order.status)}
              subtotal={Ø(() => order.subtotal.gross)}
              tax={Ø(() => order.total.tax)}
              total={Ø(() => order.total.gross)}
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
            <OrderFulfillmentDialog
              open={openedFulfillmentDialog && !!order}
              products={unfulfilled}
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
            {order && (
              <>
                <Form
                  initial={{
                    shippingMethod: {
                      label: order.shippingMethodName,
                      value: order.shippingMethod && order.shippingMethod.id
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
                  number={order.number}
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
              order.fulfillments &&
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
                            lines={Ø(() =>
                              fulfillment.lines.edges.map(edge => edge.node)
                            )}
                            status={fulfillment.status}
                            trackingCode={fulfillment.trackingNumber}
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
                              trackingCode: fulfillment.trackingNumber
                            }}
                          >
                            {({ change, data }) => (
                              <OrderFulfillmentTrackingDialog
                                open={openedTrackingDialog}
                                trackingCode={data.trackingCode}
                                variant={
                                  fulfillment.trackingNumber ? "edit" : "add"
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
            <OrderHistory history={Ø(() => order.events)} user={user} />
          </div>
          <div>
            <OrderCustomer
              billingAddress={Ø(() => order.billingAddress)}
              client={Ø(() => order.user)}
              editCustomer={isDraft}
              shippingAddress={Ø(() => order.shippingAddress)}
              onBillingAddressEdit={this.toggleBillingAddressEditDialog}
              onCustomerEditClick={this.toggleCustomerEditDialog}
              onCustomerEmailClick={onCustomerEmailClick}
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
                  initial={
                    order &&
                    order.shippingAddress &&
                    transformAddressToForm(order.shippingAddress)
                  }
                >
                  {({ change, data, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      open={openedShippingAddressEditDialog}
                      variant="shipping"
                      onClose={this.toggleShippingAddressEditDialog}
                      onConfirm={submit}
                      onChange={change}
                    />
                  )}
                </Form>
                <Form
                  initial={
                    order.billingAddress &&
                    transformAddressToForm(order.billingAddress)
                  }
                >
                  {({ change, data, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      open={openedBillingAddressEditDialog}
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
