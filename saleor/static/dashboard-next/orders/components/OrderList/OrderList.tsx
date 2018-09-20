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
import { maybe, renderCollection } from "../../../misc";

interface OrderListProps extends ListProps {
  orders?: Array<{
    id: string;
    number: string;
    status: {
      status: string;
      localized: string;
    };
    userEmail: string;
    created: string;
    paymentStatus: {
      status: string;
      localized: string;
    };
    total: {
      gross: {
        amount: number;
        currency: string;
      };
    };
  }>;
}

const decorate = withStyles(
  theme => ({
    link: {
      color: theme.palette.secondary.main,
      cursor: "pointer",
      textDecoration: "none"
    },
    textRight: {
      textAlign: "right" as "right"
    }
  }),
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
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("#", { context: "object" })}</TableCell>
            <TableCell>
              {i18n.t("Fulfillment", { context: "object" })}
            </TableCell>
            <TableCell>{i18n.t("Client", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Created at", { context: "object" })}</TableCell>
            <TableCell>
              {i18n.t("Payment status", { context: "object" })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Price", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={6}
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
            orders,
            order => (
              <TableRow key={order ? order.id : "skeleton"}>
                <TableCell
                  onClick={order && onRowClick && onRowClick(order.id)}
                  className={classes.link}
                >
                  {order ? order.number : <Skeleton />}
                </TableCell>
                <TableCell>
                  {order && order.status ? (
                    <StatusLabel
                      status={order.status.status}
                      label={order.status.localized}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>{order ? order.userEmail : <Skeleton />}</TableCell>
                <TableCell>
                  {order ? (
                    <DateFormatter date={order.created} />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
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
                <TableCell className={classes.textRight}>
                  {order && order.total && order.total.gross ? (
                    <Money
                      amount={order.total.gross.amount}
                      currency={order.total.gross.currency}
                    />
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
  )
);
export default OrderList;
