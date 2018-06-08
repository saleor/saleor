import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Money from "../../../components/Money/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface CustomerOrdersProps {
  orders?: Array<{
    id: string;
    number: number;
    orderStatus: {
      localized: string;
      status: string;
    };
    created: string;
    price: {
      amount: number;
      currency: string;
    };
  }>;
  dateNow?: number;
  hasPreviousPage?: boolean;
  hasNextPage?: boolean;
  onPreviousPage?();
  onNextPage?();
  onRowClick?(id: string);
}

const decorate = withStyles(theme => ({
  link: {
    color: blue[500],
    cursor: "pointer",
    textDecoration: "none"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const CustomerOrders = decorate<CustomerOrdersProps>(
  ({
    classes,
    dateNow,
    hasNextPage,
    hasPreviousPage,
    orders,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("#", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Created", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Status", { context: "object" })}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Price", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
              hasNextPage={hasNextPage || false}
              onNextPage={onNextPage}
              hasPreviousPage={hasPreviousPage || false}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {orders === undefined || orders === null ? (
            <TableRow>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : orders.length > 0 ? (
            orders.map(order => (
              <TableRow key={order.id}>
                <TableCell
                  onClick={onRowClick ? onRowClick(order.id) : undefined}
                  className={onRowClick ? classes.link : ""}
                >
                  {order.number}
                </TableCell>
                <TableCell>
                  <DateFormatter date={order.created} dateNow={dateNow} />
                </TableCell>
                <TableCell>
                  <StatusLabel
                    status={order.orderStatus.status}
                    label={order.orderStatus.localized}
                  />
                </TableCell>
                <TableCell className={classes.textRight}>
                  <Money
                    amount={order.price.amount}
                    currency={order.price.currency}
                  />
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={4}>{i18n.t("No orders found")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
export default CustomerOrders;
