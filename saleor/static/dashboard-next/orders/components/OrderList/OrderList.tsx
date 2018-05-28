import Card from "material-ui/Card";
import blue from "material-ui/colors/blue";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableRow
} from "material-ui/Table";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface OrderListProps {
  orders?: Array<{
    id: string;
    number: number;
    orderStatus: {
      localized: string;
      status: string;
    };
    client: {
      id: string;
      email: string;
    };
    created: string;
    paymentStatus: {
      localized: string;
      status: string;
    };
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
  currency: {
    color: theme.palette.grey[400]
  },
  link: {
    color: blue[500],
    cursor: "pointer",
    textDecoration: "none"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
export const OrderList = decorate<OrderListProps>(
  ({
    classes,
    dateNow,
    orders,
    hasPreviousPage,
    onPreviousPage,
    hasNextPage,
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
                  <StatusLabel
                    status={order.orderStatus.status}
                    label={order.orderStatus.localized}
                  />
                </TableCell>
                <TableCell>{order.client.email}</TableCell>
                <TableCell>
                  <DateFormatter date={order.created} dateNow={dateNow} />
                </TableCell>
                <TableCell>
                  <StatusLabel
                    status={order.paymentStatus.status}
                    label={order.paymentStatus.localized}
                  />
                </TableCell>
                <TableCell className={classes.textRight}>
                  {order.price.amount.toFixed(2)}{" "}
                  <span className={classes.currency}>
                    {order.price.currency}
                  </span>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6}>{i18n.t("No orders found")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
export default OrderList;
