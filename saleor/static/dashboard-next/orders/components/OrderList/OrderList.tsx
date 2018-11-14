import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { ListProps } from "../../..";
import DateFormatter from "../../../components/DateFormatter";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import {
  maybe,
  renderCollection,
  transformOrderStatus,
  transformPaymentStatus
} from "../../../misc";
import { OrderList_orders_edges_node } from "../../types/OrderList";

interface OrderListProps extends ListProps {
  orders: OrderList_orders_edges_node[];
}

const decorate = withStyles(
  {
    link: {
      cursor: "pointer"
    },
    textRight: {
      textAlign: "right" as "right"
    }
  },
  { name: "OrderList" }
);
export const OrderList = decorate<OrderListProps>(
  ({
    classes,
    disabled,
    orders,
    pageInfo,
    onPreviousPage,
    onNextPage,
    onRowClick
  }) => {
    const orderList = orders
      ? orders.map(order => ({
          ...order,
          paymentStatus: transformPaymentStatus(order.paymentStatus),
          status: transformOrderStatus(order.status)
        }))
      : undefined;
    return (
      <Card>
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
                {i18n.t("Customer", { context: "table header" })}
              </TableCell>
              <TableCell padding="dense">
                {i18n.t("Payment", { context: "table header" })}
              </TableCell>
              <TableCell padding="dense">
                {i18n.t("Fulfillment status", { context: "table header" })}
              </TableCell>
              <TableCell className={classes.textRight} padding="dense">
                {i18n.t("Total", { context: "table header" })}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableFooter>
            <TableRow>
              <TablePagination
                colSpan={6}
                hasNextPage={
                  pageInfo && !disabled ? pageInfo.hasNextPage : false
                }
                onNextPage={onNextPage}
                hasPreviousPage={
                  pageInfo && !disabled ? pageInfo.hasPreviousPage : false
                }
                onPreviousPage={onPreviousPage}
              />
            </TableRow>
          </TableFooter>
          <TableBody>
            {renderCollection(
              orderList,
              order => (
                <TableRow
                  hover={!!order}
                  className={!!order ? classes.link : undefined}
                  onClick={order ? onRowClick(order.id) : undefined}
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
                      <DateFormatter date={order.created} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell padding="dense">
                    {maybe(() => order.billingAddress) ? (
                      <>
                        {order.billingAddress.firstName}
                        &nbsp;
                        {order.billingAddress.lastName}
                      </>
                    ) : maybe(() => order.userEmail) !== undefined ? (
                      order.userEmail
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
                  <TableCell padding="dense">
                    {maybe(() => order.status) ? (
                      <StatusLabel
                        status={order.status.status}
                        label={order.status.localized}
                      />
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
OrderList.displayName = "OrderList";
export default OrderList;
