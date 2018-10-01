import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import * as React from "react";

import { transformOrderStatus } from "../..";
import CardTitle from "../../../components/CardTitle";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import i18n from "../../../i18n";
import { OrderStatus, PaymentStatusEnum } from "../../../types/globalTypes";
import OrderProducts, {
  OrderProductsProps
} from "../OrderProducts/OrderProducts";

export interface OrderSummaryProps extends OrderProductsProps {
  paymentStatus?: string;
  paymentVariant?: string;
  status?: OrderStatus;
  onCapture?();
  onCreate?();
  onFulfill?();
  onOrderCancel?();
  onProductAdd?();
  onRefund?();
  onRelease?();
  onShippingMethodClick?();
}

const OrderSummary: React.StatelessComponent<OrderSummaryProps> = ({
  authorized,
  lines,
  paid,
  paymentStatus,
  shippingMethodName,
  shippingPrice,
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
      ? paymentStatus === PaymentStatusEnum.PREAUTH &&
        !([OrderStatus.DRAFT, OrderStatus.CANCELED] as any).includes(status)
      : false;
  const canRelease =
    paymentStatus && status
      ? paymentStatus === PaymentStatusEnum.PREAUTH
      : false;
  const canRefund =
    paymentStatus && status
      ? paymentStatus === PaymentStatusEnum.CONFIRMED
      : false;
  const canFulfill = [
    OrderStatus.UNFULFILLED,
    OrderStatus.PARTIALLY_FULFILLED
  ].includes(status);
  const canCancel = status !== OrderStatus.CANCELED;
  const canGetInvoice = paymentStatus === PaymentStatusEnum.CONFIRMED;
  const isDraft = status === OrderStatus.DRAFT;
  return (
    <Card>
      <CardTitle
        title={i18n.t("Order Summary")}
        toolbar={
          isDraft && (
            <Button color="secondary" variant="flat" onClick={onProductAdd}>
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
        authorized={authorized}
        isDraft={isDraft}
        lines={lines}
        paid={paid}
        shippingMethodName={shippingMethodName}
        shippingPrice={shippingPrice}
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
              <Button onClick={onCreate}>{i18n.t("Finalize")}</Button>
            ) : (
              <>
                {canGetInvoice && <Button>{i18n.t("Invoice")}</Button>}
                {canFulfill && (
                  <Button onClick={onFulfill}>{i18n.t("Fulfill")}</Button>
                )}
                {canCapture && (
                  <Button onClick={onCapture}>{i18n.t("Capture")}</Button>
                )}
                {canRefund && (
                  <Button onClick={onRefund}>{i18n.t("Refund")}</Button>
                )}
                {canRelease && (
                  <Button onClick={onRelease}>{i18n.t("Release")}</Button>
                )}
                {canCancel && (
                  <Button onClick={onOrderCancel}>
                    {i18n.t("Cancel order")}
                  </Button>
                )}
              </>
            )}
          </CardActions>
        )}
    </Card>
  );
};
export default OrderSummary;
