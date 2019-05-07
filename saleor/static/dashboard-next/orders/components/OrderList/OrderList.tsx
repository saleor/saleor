import Checkbox from "@material-ui/core/Checkbox";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { DateTime } from "../../../components/Date";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import {
  maybe,
  renderCollection,
  transformOrderStatus,
  transformPaymentStatus
} from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { OrderList_orders_edges_node } from "../../types/OrderList";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colCustomer: {
        width: 220
      },
      colDate: {},
      colFulfillment: {
        width: 230
      },
      colNumber: {
        width: 120
      },
      colPayment: {
        width: 220
      },
      colTotal: {}
    },
    colCustomer: {},
    colDate: {},
    colFulfillment: {},
    colNumber: {},
    colPayment: {},
    colTotal: {
      textAlign: "right"
    },
    link: {
      cursor: "pointer"
    }
  });

interface OrderListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
  orders: OrderList_orders_edges_node[];
}

export const OrderList = withStyles(styles, { name: "OrderList" })(
  ({
    classes,
    disabled,
    orders,
    pageInfo,
    onPreviousPage,
    onNextPage,
    onRowClick,
    isChecked,
    selected,
    toggle,
    toolbar
  }: OrderListProps) => {
    const orderList = orders
      ? orders.map(order => ({
          ...order,
          paymentStatus: transformPaymentStatus(order.paymentStatus),
          status: transformOrderStatus(order.status)
        }))
      : undefined;
    return (
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell padding="dense" className={classes.colNumber}>
              {i18n.t("No. of Order", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense" className={classes.colDate}>
              {i18n.t("Date", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense" className={classes.colCustomer}>
              {i18n.t("Customer", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense" className={classes.colPayment}>
              {i18n.t("Payment", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense" className={classes.colFulfillment}>
              {i18n.t("Fulfillment status", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colTotal} padding="dense">
              {i18n.t("Total", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={7}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
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
            order => {
              const isSelected = order ? isChecked(order.id) : false;

              return (
                <TableRow
                  hover={!!order}
                  className={!!order ? classes.link : undefined}
                  onClick={order ? onRowClick(order.id) : undefined}
                  key={order ? order.id : "skeleton"}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(order.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell padding="dense" className={classes.colNumber}>
                    {maybe(() => order.number) ? (
                      "#" + order.number
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell padding="dense" className={classes.colDate}>
                    {maybe(() => order.created) ? (
                      <DateTime date={order.created} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell padding="dense" className={classes.colCustomer}>
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
                  <TableCell padding="dense" className={classes.colPayment}>
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
                  <TableCell padding="dense" className={classes.colFulfillment}>
                    {maybe(() => order.status) ? (
                      <StatusLabel
                        status={order.status.status}
                        label={order.status.localized}
                      />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colTotal} padding="dense">
                    {maybe(() => order.total.gross) ? (
                      <Money money={order.total.gross} />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={7}>{i18n.t("No orders found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    );
  }
);
OrderList.displayName = "OrderList";
export default OrderList;
