import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import KeyboardArrowRight from "@material-ui/icons/KeyboardArrowRight";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

// There is no API for this component right now,
// but maybe it will come in handy in the future

interface HomeNotificationTableProps {
  disabled: boolean;
  notifications: {
    orders: number;
    payments: number;
    problems: number;
    productsOut: number;
  };
  toOrders: () => void;
  toPayments: () => void;
  toProblems: () => void;
  toProductsOut: () => void;
}

const decorate = withStyles(theme => ({
  arrowIcon: {
    width: theme.spacing.unit * 4
  },
  tableRow: {
    cursor: "pointer" as "pointer"
  }
}));
const HomeNotificationTable = decorate<HomeNotificationTableProps>(
  ({
    classes,
    notifications,
    toOrders,
    toPayments,
    toProblems,
    toProductsOut
  }) => {
    return (
      <Card>
        <Table>
          <TableBody className={classes.tableRow}>
            <TableRow
              hover={true}
              onClick={!!notifications ? toOrders : undefined}
            >
              <TableCell>
                {notifications === undefined ? (
                  <Skeleton />
                ) : notifications && notifications.orders === 0 ? (
                  <Typography>{i18n.t("No orders to fulfill")}</Typography>
                ) : (
                  <Typography
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "<b>{{orders}} Orders</b> are ready to fulfill",
                        { orders: notifications.orders }
                      )
                    }}
                  />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow
              hover={true}
              onClick={!!notifications ? toPayments : undefined}
            >
              <TableCell>
                {notifications === undefined ? (
                  <Skeleton />
                ) : notifications.payments === 0 ? (
                  <Typography>
                    {i18n.t("No payments waiting for capture")}
                  </Typography>
                ) : (
                  <Typography
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "<b>{{payments}} Payments </b>to capture",
                        { payments: notifications.payments }
                      )
                    }}
                  />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow
              hover={true}
              onClick={!!notifications ? toProblems : undefined}
            >
              <TableCell>
                {notifications === undefined ? (
                  <Skeleton />
                ) : notifications.problems === 0 ? (
                  <Typography>{i18n.t("No problem with orders")}</Typography>
                ) : (
                  <Typography
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "<b>{{problems}} Problems</b>  with orders",
                        { problems: notifications.problems }
                      )
                    }}
                  />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow
              hover={true}
              onClick={!!notifications ? toProductsOut : undefined}
            >
              <TableCell>
                {notifications === undefined ? (
                  <Skeleton />
                ) : notifications.productsOut === 0 ? (
                  <Typography>{i18n.t("No out of stock products")}</Typography>
                ) : (
                  <Typography
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "<b>{{productsOut}} Products </b>out of stock",
                        { productsOut: notifications.productsOut }
                      )
                    }}
                  />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>
    );
  }
);
export default HomeNotificationTable;
