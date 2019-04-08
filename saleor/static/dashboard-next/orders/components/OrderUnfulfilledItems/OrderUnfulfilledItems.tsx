import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderDetails_order_lines } from "../../types/OrderDetails";

const styles = createStyles({
  clickableRow: {
    cursor: "pointer"
  },
  textCenter: {
    textAlign: "center"
  },
  textRight: {
    textAlign: "right"
  },
  wideCell: {
    width: "50%"
  }
});

interface OrderUnfulfilledItemsProps extends WithStyles<typeof styles> {
  canFulfill: boolean;
  lines: OrderDetails_order_lines[];
  onFulfill: () => void;
}

const OrderUnfulfilledItems = withStyles(styles, {
  name: "OrderUnfulfilledItems"
})(({ canFulfill, classes, lines, onFulfill }: OrderUnfulfilledItemsProps) => (
  <Card>
    <CardTitle
      title={
        <StatusLabel
          label={i18n.t("Unfulfilled ({{ quantity }})", {
            quantity: lines
              .map(line => line.quantity - line.quantityFulfilled)
              .reduce((prev, curr) => prev + curr, 0)
          })}
          status="error"
        />
      }
    />
    <Table>
      <TableHead>
        <TableRow>
          <TableCell className={classes.wideCell} colSpan={2}>
            {i18n.t("Product")}
          </TableCell>
          <TableCell className={classes.textCenter}>
            {i18n.t("Quantity")}
          </TableCell>
          <TableCell className={classes.textRight}>{i18n.t("Price")}</TableCell>
          <TableCell className={classes.textRight}>{i18n.t("Total")}</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {lines.map(line => (
          <TableRow
            className={!!line ? classes.clickableRow : undefined}
            hover={!!line}
            key={maybe(() => line.id)}
          >
            <TableCellAvatar thumbnail={line.thumbnailUrl} />
            <TableCell>
              {maybe(() => line.productName) || <Skeleton />}
            </TableCell>
            <TableCell className={classes.textCenter}>
              {maybe(() => line.quantity - line.quantityFulfilled) || (
                <Skeleton />
              )}
            </TableCell>
            <TableCell className={classes.textRight}>
              {maybe(() => line.unitPrice.gross) ? (
                <Money money={line.unitPrice.gross} />
              ) : (
                <Skeleton />
              )}
            </TableCell>
            <TableCell className={classes.textRight}>
              {maybe(
                () =>
                  (line.quantity - line.quantityFulfilled) *
                  line.unitPrice.gross.amount
              ) ? (
                <Money
                  money={{
                    amount:
                      (line.quantity - line.quantityFulfilled) *
                      line.unitPrice.gross.amount,
                    currency: line.unitPrice.gross.currency
                  }}
                />
              ) : (
                <Skeleton />
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
    {canFulfill && (
      <CardActions>
        <Button variant="text" color="primary" onClick={onFulfill}>
          {i18n.t("Fulfill", {
            context: "button"
          })}
        </Button>
      </CardActions>
    )}
  </Card>
));
OrderUnfulfilledItems.displayName = "OrderUnfulfilledItems";
export default OrderUnfulfilledItems;
