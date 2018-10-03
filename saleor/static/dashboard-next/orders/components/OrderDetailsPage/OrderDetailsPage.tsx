import { withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AddressType, transformAddressToForm } from "../..";
import { UserError } from "../../..";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import Toggle from "../../../components/Toggle";
import { AddressTypeInput } from "../../../customers";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderEvents, OrderStatus } from "../../../types/globalTypes";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCancelDialog, {
  FormData as OrderCancelFormData
} from "../OrderCancelDialog";
import OrderCustomer from "../OrderCustomer";
import OrderCustomerEditDialog from "../OrderCustomerEditDialog";
import OrderFulfillment from "../OrderFulfillment";
import OrderFulfillmentCancelDialog from "../OrderFulfillmentCancelDialog";
import OrderFulfillmentDialog, {
  FormData as OrderFulfillFormData
} from "../OrderFulfillmentDialog";
import OrderFulfillmentTrackingDialog from "../OrderFulfillmentTrackingDialog";
import OrderHistory, { FormData as HistoryFormData } from "../OrderHistory";
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
    lines: Array<{
      id: string;
      productName: string;
      productSku: string;
      thumbnailUrl: string;
      unitPrice: TaxedMoneyType;
      quantity: number;
      quantityFulfilled: number;
    }>;
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
  errors: UserError[];
  fetchUsers?(value: string);
  fetchVariants?(value: string);
  onBack();
  onBillingAddressEdit(data: AddressTypeInput);
  onCreate?();
  onOrderFulfill(data: OrderFulfillFormData);
  onOrderLineChange(id: string): (value: string) => void;
  onOrderLineRemove(id: string);
  onProductAdd(data: ProductAddFormData);
  onProductClick?(id: string);
  onPackingSlipClick?(id: string);
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
      errors,
      order,
      shippingMethods,
      user,
      users,
      variants,
      variantsLoading,
      fetchUsers,
      fetchVariants,
      onBack,
      onBillingAddressEdit,
      onCreate,
      onNoteAdd,
      onOrderCancel,
      onOrderFulfill,
      onOrderLineChange,
      onOrderLineRemove,
      onPackingSlipClick,
      onPaymentCapture,
      onPaymentRefund,
      onPaymentRelease,
      onProductAdd,
      onProductClick,
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
              authorized={maybe(() => order.totalAuthorized)}
              paid={maybe(() => order.totalCaptured)}
              paymentStatus={maybe(() => order.paymentStatus)}
              lines={maybe(() => order.lines)}
              shippingMethodName={maybe(() => order.shippingMethodName)}
              shippingPrice={maybe(() => order.shippingPrice)}
              status={maybe(() => order.status)}
              subtotal={maybe(() => order.subtotal.gross)}
              tax={maybe(() => order.total.tax)}
              total={maybe(() => order.total.gross)}
              onCapture={this.togglePaymentCaptureDialog}
              onCreate={onCreate}
              onFulfill={this.toggleFulfillmentDialog}
              onOrderCancel={this.toggleOrderCancelDialog}
              onOrderLineChange={isDraft ? onOrderLineChange : undefined}
              onOrderLineRemove={onOrderLineRemove}
              onProductAdd={this.toggleOrderProductAddDialog}
              onRefund={this.togglePaymentRefundDialog}
              onRelease={this.togglePaymentReleaseDialog}
              onRowClick={onProductClick}
              onShippingMethodClick={this.toggleShippingMethodEditDialog}
            />
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
            {order && (
              <>
                <OrderCancelDialog
                  number={order.number}
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
                            lines={maybe(() =>
                              fulfillment.lines.edges.map(edge => edge.node)
                            )}
                            status={fulfillment.status}
                            trackingCode={fulfillment.trackingNumber}
                            onOrderFulfillmentCancel={toggleCancelDialog}
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
            <OrderHistory
              history={maybe(() => order.events)}
              user={user}
              onNoteAdd={onNoteAdd}
            />
          </div>
          <div>
            <OrderCustomer
              billingAddress={maybe(() => order.billingAddress)}
              client={maybe(() => order.user)}
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
    );
  }
}
const OrderDetailsPage = decorate<OrderDetailsPageProps>(
  OrderDetailsPageComponent
);
export default OrderDetailsPage;
