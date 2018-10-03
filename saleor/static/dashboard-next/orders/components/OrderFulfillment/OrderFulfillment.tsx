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

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { FulfillmentStatus } from "../../../types/globalTypes";
import { OrderDetails_order_fulfillments } from "../../types/OrderDetails";

interface OrderFulfillmentProps {
  fulfillment: OrderDetails_order_fulfillments;
  onOrderFulfillmentCancel();
  onTrackingCodeAdd();
}

const decorate = withStyles(
  theme => ({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit * 3,
      width: theme.spacing.unit * 5
    },
    root: {
      marginTop: theme.spacing.unit * 2,
      [theme.breakpoints.down("sm")]: {
        marginTop: theme.spacing.unit
      }
    },
    statusBar: {
      paddingTop: 0
    },
    textLeft: {
      textAlign: [["left"], "!important"] as any
    }
  }),
  { name: "OrderFulfillment" }
);
const OrderFulfillment = decorate<OrderFulfillmentProps>(
  ({ classes, fulfillment, onOrderFulfillmentCancel, onTrackingCodeAdd }) => {
    const lines = maybe(() => fulfillment.lines.edges.map(edge => edge.node));
    const status = maybe(() => fulfillment.status);
    return (
      <Card className={classes.root}>
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
        />
        <Table>
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell className={classes.textLeft}>
                {i18n.t("Product")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {lines ? (
              lines.map(productLine => (
                <TableRow key={productLine.orderLine.id}>
                  <TableCellAvatar
                    thumbnail={productLine.orderLine.thumbnailUrl}
                  />
                  <TableCell className={classes.textLeft}>
                    {productLine.orderLine.productName} x {productLine.quantity}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCellAvatar />
                <TableCell>
                  <Skeleton />
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        {status === FulfillmentStatus.FULFILLED && (
          <CardActions>
            <Button onClick={onTrackingCodeAdd}>
              {fulfillment.trackingNumber
                ? i18n.t("Add tracking number")
                : i18n.t("Edit tracking number")}
            </Button>
            <Button onClick={onOrderFulfillmentCancel}>
              {i18n.t("Cancel shipment")}
            </Button>
          </CardActions>
        )}
      </Card>
    );
  }
);
export default OrderFulfillment;
