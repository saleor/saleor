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
import { maybe } from "../../../misc";

interface HomeNotificationTableProps {
  ordersToCapture: number;
  ordersToFulfill: number;
  productsOutOfStock: number;
  onOrdersToFulfillClick: () => void;
  onOrdersToCaptureClick: () => void;
  onProductsOutOfStockClick: () => void;
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
    onOrdersToCaptureClick,
    onOrdersToFulfillClick,
    onProductsOutOfStockClick,
    ordersToCapture,
    ordersToFulfill,
    productsOutOfStock
  }) => {
    return (
      <Card>
        <Table>
          <TableBody className={classes.tableRow}>
            <TableRow hover={true} onClick={onOrdersToFulfillClick}>
              <TableCell>
                {maybe(
                  () =>
                    ordersToFulfill === 0 ? (
                      <Typography>
                        {i18n.t("No orders ready to fulfill")}
                      </Typography>
                    ) : (
                      <Typography
                        dangerouslySetInnerHTML={{
                          __html: i18n.t(
                            "<b>{{ amount }} Orders</b> are ready to fulfill",
                            { amount: ordersToFulfill }
                          )
                        }}
                      />
                    ),
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow hover={true} onClick={onOrdersToCaptureClick}>
              <TableCell>
                {maybe(
                  () =>
                    ordersToCapture === 0 ? (
                      <Typography>
                        {i18n.t("No payments waiting for capture")}
                      </Typography>
                    ) : (
                      <Typography
                        dangerouslySetInnerHTML={{
                          __html: i18n.t(
                            "<b>{{ amount }} Payments</b> to capture",
                            { amount: ordersToCapture }
                          )
                        }}
                      />
                    ),
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow hover={true} onClick={onProductsOutOfStockClick}>
              <TableCell>
                {maybe(
                  () =>
                    productsOutOfStock === 0 ? (
                      <Typography>
                        {i18n.t("No products out of stock")}
                      </Typography>
                    ) : (
                      <Typography
                        dangerouslySetInnerHTML={{
                          __html: i18n.t(
                            "<b>{{ amount }} Products</b> out of stock",
                            { amount: productsOutOfStock }
                          )
                        }}
                      />
                    ),
                  <Skeleton />
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
