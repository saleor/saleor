import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { DateTime } from "../../../components/Date";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import i18n from "../../../i18n";
import { maybe, renderCollection, transformPaymentStatus } from "../../../misc";
import { CustomerDetails_user_orders_edges_node } from "../../types/CustomerDetails";

const styles = createStyles({
  link: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  }
});

export interface CustomerOrdersProps extends WithStyles<typeof styles> {
  orders: CustomerDetails_user_orders_edges_node[];
  onViewAllOrdersClick: () => void;
  onRowClick: (id: string) => void;
}

const CustomerOrders = withStyles(styles, { name: "CustomerOrders" })(
  ({
    classes,
    orders,
    onRowClick,
    onViewAllOrdersClick
  }: CustomerOrdersProps) => {
    const orderList = orders
      ? orders.map(order => ({
          ...order,
          paymentStatus: transformPaymentStatus(order.paymentStatus)
        }))
      : undefined;
    return (
      <Card>
        <CardTitle
          title={i18n.t("Recent orders")}
          toolbar={
            <Button
              variant="text"
              color="primary"
              onClick={onViewAllOrdersClick}
            >
              {i18n.t("View all orders")}
            </Button>
          }
        />
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="dense">
                {i18n.t("No. of Order", { context: "table header" })}
              </TableCell>
              <TableCell padding="dense">
                {i18n.t("Date", { context: "table header" })}
              </TableCell>
              <TableCell padding="dense">
                {i18n.t("Status", { context: "table header" })}
              </TableCell>
              <TableCell className={classes.textRight} padding="dense">
                {i18n.t("Total", { context: "table header" })}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {renderCollection(
              orderList,
              order => (
                <TableRow
                  hover={!!order}
                  className={!!order ? classes.link : undefined}
                  onClick={order ? () => onRowClick(order.id) : undefined}
                  key={order ? order.id : "skeleton"}
                >
                  <TableCell padding="dense">
                    {maybe(() => order.number) ? (
                      "#" + order.number
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell padding="dense">
                    {maybe(() => order.created) ? (
                      <DateTime date={order.created} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell padding="dense">
                    {maybe(() => order.paymentStatus.status) !== undefined ? (
                      order.paymentStatus.status === null ? null : (
                        <StatusLabel
                          status={order.paymentStatus.status}
                          label={order.paymentStatus.localized}
                        />
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.textRight} padding="dense">
                    {maybe(() => order.total.gross) ? (
                      <Money money={order.total.gross} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              ),
              () => (
                <TableRow>
                  <TableCell colSpan={6}>{i18n.t("No orders found")}</TableCell>
                </TableRow>
              )
            )}
          </TableBody>
        </Table>
      </Card>
    );
  }
);
CustomerOrders.displayName = "CustomerOrders";
export default CustomerOrders;
