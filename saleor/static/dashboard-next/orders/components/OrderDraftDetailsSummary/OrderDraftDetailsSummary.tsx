import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import Link from "../../../components/Link";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderDetails_order } from "../../types/OrderDetails";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      ...theme.typography.body1,
      lineHeight: 1.9,
      width: "100%"
    },
    textRight: {
      textAlign: "right"
    }
  });

interface OrderDraftDetailsSummaryProps extends WithStyles<typeof styles> {
  order: OrderDetails_order;
  onShippingMethodEdit: () => void;
}

const OrderDraftDetailsSummary = withStyles(styles, {
  name: "OrderDraftDetailsSummary"
})(
  ({ classes, order, onShippingMethodEdit }: OrderDraftDetailsSummaryProps) => (
    <table className={classes.root}>
      <tbody>
        <tr>
          {maybe(() => order.subtotal) ? (
            <>
              <td>{i18n.t("Subtotal")}</td>
              <td className={classes.textRight}>
                <Money money={order.subtotal.gross} />
              </td>
            </>
          ) : (
            <td colSpan={2}>
              <Skeleton />
            </td>
          )}
        </tr>
        <tr>
          {order &&
          order.shippingMethod !== undefined &&
          order.shippingMethodName !== undefined ? (
            order.shippingMethod === null ? (
              order.availableShippingMethods &&
              order.availableShippingMethods.length > 0 ? (
                <td>
                  <Link onClick={onShippingMethodEdit}>
                    {i18n.t("Add shipping carrier")}
                  </Link>
                </td>
              ) : (
                <td>{i18n.t("No applicable shipping carriers")}</td>
              )
            ) : (
              <>
                <td>
                  <Link onClick={onShippingMethodEdit}>
                    {order.shippingMethodName}
                  </Link>
                </td>
                <td className={classes.textRight}>
                  {maybe(() => order.shippingPrice) ? (
                    <Money money={order.shippingPrice.gross} />
                  ) : (
                    "---"
                  )}
                </td>
              </>
            )
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
                <Money money={order.total.tax} />
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
                <Money money={order.total.gross} />
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
