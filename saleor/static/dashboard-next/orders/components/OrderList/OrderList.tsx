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

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface OrderListProps {
  orders?: Array<{
    id: string;
    number: number;
    status: string;
    client: {
      id: string;
      email: string;
    };
    created: string;
    paymentStatus: string;
    price: {
      localized;
    };
  }>;
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
const OrderList = decorate<OrderListProps>(
  ({
    classes,
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
            <TableCell>{i18n.t("Status", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Client", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Created at", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Payment", { context: "object" })}</TableCell>
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
                  onClick={onRowClick ? onRowClick(order.id) : () => {}}
                  className={classes.link}
                >
                  {order.number}
                </TableCell>
                <TableCell>{order.status}</TableCell>
                <TableCell>{order.client.email}</TableCell>
                <TableCell>{order.created}</TableCell>
                <TableCell>{order.paymentStatus}</TableCell>
                <TableCell className={classes.textRight}>
                  {order.price.localized}
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
