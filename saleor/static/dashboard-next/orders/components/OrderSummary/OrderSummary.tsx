import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import { transformOrderStatus } from "../..";
import PageHeader from "../../../components/PageHeader";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import i18n from "../../../i18n";
import OrderProducts, {
  OrderProductsProps
} from "../OrderProducts/OrderProducts";

interface MoneyType {
  amount: number;
  currency: string;
}
interface OrderSummaryProps extends OrderProductsProps {
  status?: string;
  onFulfill?();
  onPaymentOperation?();
  onOrderCancel?();
}

const decorate = withStyles(theme => ({
  root: {},
  hr: {
    height: 1,
    display: "block",
    border: "none",
    width: "100%",
    backgroundColor: theme.palette.grey[200]
  },
  cardActions: {
    direction: "rtl" as "rtl"
  },
  statusBar: {
    paddingTop: 0
  }
}));
const OrderSummary = decorate<OrderSummaryProps>(
  ({
    classes,
    products,
    subtotal,
    total,
    status,
    paid,
    refunded,
    net,
    onRowClick,
    onFulfill,
    onPaymentOperation,
    onOrderCancel
  }) => {
    const orderStatus = status ? transformOrderStatus(status) : undefined;
    return (
      <Card>
        <PageHeader title={i18n.t("Order Summary")} />
        {status && (
          <CardContent className={classes.statusBar}>
            <StatusLabel
              status={orderStatus.status}
              label={orderStatus.localized}
            />
          </CardContent>
        )}
        <OrderProducts
          products={products}
          subtotal={subtotal}
          total={total}
          paid={paid}
          refunded={refunded}
          net={net}
          onRowClick={onRowClick}
        />
        <CardActions className={classes.cardActions}>
          {status && (
            <>
              {orderStatus.status !== "success" && (
                <Button disabled={!onFulfill} onClick={onFulfill}>
                  {i18n.t("Fulfill")}
                </Button>
              )}
              {!(paid.amount > 0 && refunded.amount > 0) && (
                <Button
                  disabled={!onPaymentOperation}
                  onClick={onPaymentOperation}
                >
                  {paid.amount === 0 ? i18n.t("Capture") : i18n.t("Refund")}
                </Button>
              )}
            </>
          )}
          <Button>{i18n.t("Invoice")}</Button>
          <Button disabled={!onOrderCancel} onClick={onOrderCancel}>
            {i18n.t("Cancel order")}
          </Button>
        </CardActions>
      </Card>
    );
  }
);
export default OrderSummary;
