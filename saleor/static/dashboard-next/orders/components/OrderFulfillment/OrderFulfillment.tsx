import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { CardMenu } from "../../../components/CardMenu/CardMenu";
import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { FulfillmentStatus } from "../../../types/globalTypes";
import { OrderDetails_order_fulfillments } from "../../types/OrderDetails";

interface OrderFulfillmentProps {
  fulfillment: OrderDetails_order_fulfillments;
  onOrderFulfillmentCancel: () => void;
  onTrackingCodeAdd: () => void;
}

const decorate = withStyles(
  {
    clickableRow: {
      cursor: "pointer" as "pointer"
    },
    statusBar: {
      paddingTop: 0
    },
    textCenter: {
      textAlign: "center" as "center"
    },
    textRight: {
      textAlign: "right" as "right"
    },
    wideCell: {
      width: "50%"
    }
  },
  { name: "OrderFulfillment" }
);
const OrderFulfillment = decorate<OrderFulfillmentProps>(
  ({ classes, fulfillment, onOrderFulfillmentCancel, onTrackingCodeAdd }) => {
    const lines = maybe(() => fulfillment.lines.edges.map(edge => edge.node));
    const status = maybe(() => fulfillment.status);
    return (
      <Card>
        <CardTitle
          title={
            <StatusLabel
              label={
                status === FulfillmentStatus.FULFILLED
                  ? i18n.t("Fulfilled ({{ quantity }})", {
                      quantity: lines
                        .map(line => line.quantity)
                        .reduce((prev, curr) => prev + curr, 0)
                    })
                  : i18n.t("Cancelled ({{ quantity }})", {
                      quantity: lines
                        .map(line => line.quantity)
                        .reduce((prev, curr) => prev + curr, 0)
                    })
              }
              status={
                status === FulfillmentStatus.FULFILLED ? "success" : "error"
              }
            />
          }
          toolbar={
            fulfillment.status === FulfillmentStatus.FULFILLED && (
              <CardMenu
                menuItems={[
                  {
                    label: i18n.t("Cancel shipment", {
                      context: "button"
                    }),
                    onSelect: onOrderFulfillmentCancel
                  }
                ]}
              />
            )
          }
        />
        <Table>
          <TableHead>
            <TableRow>
              <TableCell className={classes.wideCell} colSpan={2}>
                {i18n.t("Product")}
              </TableCell>
              <TableCell className={classes.textCenter}>
                {i18n.t("Quantity")}
              </TableCell>
              <TableCell className={classes.textRight}>
                {i18n.t("Price")}
              </TableCell>
              <TableCell className={classes.textRight}>
                {i18n.t("Total")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {lines.map(line => (
              <TableRow
                className={!!line ? classes.clickableRow : undefined}
                hover={!!line}
                key={maybe(() => line.id)}
              >
                <TableCellAvatar thumbnail={line.orderLine.thumbnailUrl} />
                <TableCell>
                  {maybe(() => line.orderLine.productName) || <Skeleton />}
                </TableCell>
                <TableCell className={classes.textCenter}>
                  {maybe(() => line.quantity) || <Skeleton />}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {maybe(() => line.orderLine.unitPrice.gross) ? (
                    <Money
                      amount={line.orderLine.unitPrice.gross.amount}
                      currency={line.orderLine.unitPrice.gross.currency}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {maybe(
                    () => line.quantity * line.orderLine.unitPrice.gross.amount
                  ) ? (
                    <Money
                      amount={
                        line.quantity * line.orderLine.unitPrice.gross.amount
                      }
                      currency={line.orderLine.unitPrice.gross.currency}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ))}
            {fulfillment.trackingNumber && (
              <TableRow>
                <TableCell colSpan={4}>
                  {i18n.t("Tracking Number: {{ trackingNumber }}", {
                    trackingNumber: fulfillment.trackingNumber
                  })}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        {status === FulfillmentStatus.FULFILLED &&
          !fulfillment.trackingNumber && (
            <CardActions>
              <Button color="secondary" onClick={onTrackingCodeAdd}>
                {i18n.t("Add tracking")}
              </Button>
            </CardActions>
          )}
      </Card>
    );
  }
);
export default OrderFulfillment;
