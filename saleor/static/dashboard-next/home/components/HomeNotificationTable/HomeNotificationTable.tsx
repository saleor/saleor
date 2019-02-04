import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import KeyboardArrowRight from "@material-ui/icons/KeyboardArrowRight";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    arrowIcon: {
      width: theme.spacing.unit * 4
    },
    tableRow: {
      cursor: "pointer"
    }
  });

interface HomeNotificationTableProps extends WithStyles<typeof styles> {
  ordersToCapture: number;
  ordersToFulfill: number;
  productsOutOfStock: number;
  onOrdersToFulfillClick: () => void;
  onOrdersToCaptureClick: () => void;
  onProductsOutOfStockClick: () => void;
}

const HomeNotificationTable = withStyles(styles, {
  name: "HomeNotificationTable"
})(
  ({
    classes,
    onOrdersToCaptureClick,
    onOrdersToFulfillClick,
    onProductsOutOfStockClick,
    ordersToCapture,
    ordersToFulfill,
    productsOutOfStock
  }: HomeNotificationTableProps) => {
    return (
      <Card>
        <Table>
          <TableBody className={classes.tableRow}>
            <TableRow hover={true} onClick={onOrdersToFulfillClick}>
              <TableCell>
                {ordersToFulfill === undefined ? (
                  <Skeleton />
                ) : ordersToFulfill === 0 ? (
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
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow hover={true} onClick={onOrdersToCaptureClick}>
              <TableCell>
                {ordersToCapture === undefined ? (
                  <Skeleton />
                ) : ordersToCapture === 0 ? (
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
                )}
              </TableCell>
              <TableCell className={classes.arrowIcon}>
                <KeyboardArrowRight />
              </TableCell>
            </TableRow>
            <TableRow hover={true} onClick={onProductsOutOfStockClick}>
              <TableCell>
                {productsOutOfStock === undefined ? (
                  <Skeleton />
                ) : productsOutOfStock === 0 ? (
                  <Typography>{i18n.t("No products out of stock")}</Typography>
                ) : (
                  <Typography
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "<b>{{ amount }} Products</b> out of stock",
                        { amount: productsOutOfStock }
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
HomeNotificationTable.displayName = "HomeNotificationTable";
export default HomeNotificationTable;
