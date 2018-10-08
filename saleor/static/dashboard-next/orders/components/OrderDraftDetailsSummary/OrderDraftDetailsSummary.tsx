import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Link from "../../../components/Link";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderDetails_order } from "../../types/OrderDetails";

interface OrderDraftDetailsSummaryProps {
  order: OrderDetails_order;
  onShippingMethodEdit: () => void;
}

const decorate = withStyles(theme => ({
  root: {
    ...theme.typography.body1,
    lineHeight: 1.9,
    width: "100%"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const OrderDraftDetailsSummary = decorate<OrderDraftDetailsSummaryProps>(
  ({ classes, order, onShippingMethodEdit }) => (
    <table className={classes.root}>
      <tbody>
        <tr>
          {maybe(() => order.subtotal) ? (
            <>
              <td>{i18n.t("Subtotal")}</td>
              <td className={classes.textRight}>
                <Money {...order.subtotal.gross} />
              </td>
            </>
          ) : (
            <td colSpan={2}>
              <Skeleton />
            </td>
          )}
        </tr>
        <tr>
          {maybe(() => order.shippingMethod) !== undefined ? (
            <>
              <td>
                <Link onClick={onShippingMethodEdit}>
                  {maybe(() => order.shippingMethodName)
                    ? order.shippingMethodName
                    : i18n.t("Add Shipping Carrier")}
                </Link>
              </td>
              <td className={classes.textRight}>
                {maybe(() => order.shippingPrice) ? (
                  <Money {...order.shippingPrice.gross} />
                ) : (
                  "---"
                )}
              </td>
            </>
          ) : (
            <td colSpan={2}>
              <Skeleton />
            </td>
          )}
        </tr>
        <tr>
          {maybe(() => order.total.tax) !== undefined ? (
            <>
              <td>{i18n.t("Taxes (VAT included)")}</td>
              <td className={classes.textRight}>
                <Money {...order.total.tax} />
              </td>
            </>
          ) : (
            <td colSpan={2}>
              <Skeleton />
            </td>
          )}
        </tr>
        <tr>
          {maybe(() => order.total.gross) !== undefined ? (
            <>
              <td>{i18n.t("Total")}</td>
              <td className={classes.textRight}>
                <Money {...order.total.gross} />
              </td>
            </>
          ) : (
            <td colSpan={2}>
              <Skeleton />
            </td>
          )}
        </tr>
      </tbody>
    </table>
  )
);
OrderDraftDetailsSummary.displayName = "OrderDraftDetailsSummary";
export default OrderDraftDetailsSummary;
