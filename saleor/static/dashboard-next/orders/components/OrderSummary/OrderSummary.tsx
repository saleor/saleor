import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import {
  OrderStatus,
  PaymentStatus,
  PaymentVariants,
  transformOrderStatus
} from "../..";
import PageHeader from "../../../components/PageHeader";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import i18n from "../../../i18n";
import OrderProducts, {
  OrderProductsProps
} from "../OrderProducts/OrderProducts";
import CardTitle from "../../../components/CardTitle";

interface MoneyType {
  amount: number;
  currency: string;
}
interface OrderSummaryProps extends OrderProductsProps {
  paymentStatus?: string;
  paymentVariant?: string;
  shippingMethod?: {
    name: string;
    price: MoneyType;
  };
  status?: string;
  onCapture?();
  onCreate?();
  onFulfill?();
  onOrderCancel?();
  onOrderLineChange?(id: string): (value: string) => () => void;
  onOrderLineRemove?(id: string): () => void;
  onProductAdd?();
  onRefund?();
  onRelease?();
  onShippingMethodClick?();
}

const decorate = withStyles(
  theme => ({
    root: {},
    hr: {
      height: 1,
      display: "block",
      border: "none",
      width: "100%",
      backgroundColor: theme.palette.grey[200]
    },
    statusBar: {
      paddingTop: 0
    }
  }),
  { name: "OrderSummary" }
);
const OrderSummary = decorate<OrderSummaryProps>(
  ({
    classes,
    net,
    paid,
    paymentStatus,
    paymentVariant,
    products,
    refunded,
    shippingMethod,
    status,
    subtotal,
    total,
    onCapture,
    onCreate,
    onFulfill,
    onOrderCancel,
    onOrderLineChange,
    onOrderLineRemove,
    onProductAdd,
    onRefund,
    onRelease,
    onRowClick,
    onShippingMethodClick
  }) => {
    const orderStatus = status ? transformOrderStatus(status) : undefined;
    const canCapture =
      paymentStatus && status
        ? paymentStatus === PaymentStatus.PREAUTH &&
          !([OrderStatus.DRAFT, OrderStatus.CANCELLED] as any).includes(status)
        : false;
    const canRelease =
      paymentStatus && status ? paymentStatus === PaymentStatus.PREAUTH : false;
    const canRefund =
      paymentStatus && status
        ? paymentStatus === PaymentStatus.CONFIRMED &&
          paymentVariant !== PaymentVariants.MANUAL
        : false;
    const canFulfill = ([
      OrderStatus.UNFULFILLED,
      OrderStatus.PARTIALLY_FULFILLED
    ] as any).includes(status);
    const canCancel = status !== OrderStatus.CANCELLED;
    const canGetInvoice = paymentStatus === PaymentStatus.CONFIRMED;
    const isDraft = status === OrderStatus.DRAFT;
    return (
      <Card>
        <CardTitle
          title={i18n.t("Order Summary")}
          toolbar={
            isDraft && (
              <Button
                color="secondary"
                variant="flat"
                disabled={!onProductAdd}
                onClick={onProductAdd}
              >
                {i18n.t("Add product")}
              </Button>
            )
          }
        >
          {status && (
            <StatusLabel
              status={orderStatus.status}
              label={orderStatus.localized}
              typographyProps={{ variant: "body1" }}
            />
          )}
        </CardTitle>
        <OrderProducts
          isDraft={isDraft}
          net={net}
          paid={paid}
          products={products}
          refunded={refunded}
          shippingMethod={shippingMethod}
          subtotal={subtotal}
          total={total}
          onOrderLineChange={onOrderLineChange}
          onOrderLineRemove={onOrderLineRemove}
          onRowClick={onRowClick}
          onShippingMethodClick={onShippingMethodClick}
        />
        {status &&
          (canGetInvoice ||
            canFulfill ||
            canCapture ||
            canRefund ||
            canRelease ||
            canCancel ||
            isDraft) && (
            <CardActions>
              {isDraft ? (
                <Button disabled={!onCreate} onClick={onCreate}>
                  {i18n.t("Finalize")}
                </Button>
              ) : (
                <>
                  {canGetInvoice && <Button>{i18n.t("Invoice")}</Button>}
                  {canFulfill && (
                    <Button disabled={!onFulfill} onClick={onFulfill}>
                      {i18n.t("Fulfill")}
                    </Button>
                  )}
                  {canCapture && (
                    <Button disabled={!onCapture} onClick={onCapture}>
                      {i18n.t("Capture")}
                    </Button>
                  )}
                  {canRefund && (
                    <Button disabled={!onRefund} onClick={onRefund}>
                      {i18n.t("Refund")}
                    </Button>
                  )}
                  {canRelease && (
                    <Button disabled={!onRelease} onClick={onRelease}>
                      {i18n.t("Release")}
                    </Button>
                  )}
                  {canCancel && (
                    <Button disabled={!onOrderCancel} onClick={onOrderCancel}>
                      {i18n.t("Cancel order")}
                    </Button>
                  )}
                </>
              )}
            </CardActions>
          )}
      </Card>
    );
  }
);
export default OrderSummary;
