import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import { DebounceForm } from "@saleor/components/DebounceForm";
import Form from "@saleor/components/Form";
import Money from "@saleor/components/Money";
import Skeleton from "@saleor/components/Skeleton";
import TableCellAvatar, {
  AVATAR_MARGIN
} from "@saleor/components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { OrderDetails_order_lines } from "../../types/OrderDetails";

export interface FormData {
  quantity: number;
}

const styles = (theme: Theme) =>
  createStyles({
    colAction: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    colName: {
      width: "auto"
    },
    colNameLabel: {
      marginLeft: AVATAR_MARGIN
    },
    colPrice: {
      textAlign: "right",
      width: 150
    },
    colQuantity: {
      textAlign: "right",
      width: 80
    },
    colTotal: {
      textAlign: "right",
      width: 150
    },
    quantityField: {
      "& input": {
        padding: "12px 12px 10px",
        textAlign: "right"
      },
      width: 60
    },
    table: {
      tableLayout: "fixed"
    }
  });

interface OrderDraftDetailsProductsProps extends WithStyles<typeof styles> {
  lines: OrderDetails_order_lines[];
  onOrderLineChange: (id: string, data: FormData) => void;
  onOrderLineRemove: (id: string) => void;
}

const OrderDraftDetailsProducts = withStyles(styles, {
  name: "OrderDraftDetailsProducts"
})(
  ({
    classes,
    lines,
    onOrderLineChange,
    onOrderLineRemove
  }: OrderDraftDetailsProductsProps) => (
    <Table className={classes.table}>
      {maybe(() => !!lines.length) && (
        <TableHead>
          <TableRow>
            <TableCell className={classes.colName}>
              <span className={classes.colNameLabel}>
                {i18n.t("Product", { context: "table header" })}
              </span>
            </TableCell>
            <TableCell className={classes.colQuantity}>
              {i18n.t("Quantity", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colPrice}>
              {i18n.t("Price", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colTotal}>
              {i18n.t("Total", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colAction} />
          </TableRow>
        </TableHead>
      )}
      <TableBody>
        {maybe(() => lines.length) === 0 ? (
          <TableRow>
            <TableCell colSpan={5}>
              {i18n.t("No Products added to Order")}
            </TableCell>
          </TableRow>
        ) : (
          renderCollection(lines, line => (
            <TableRow key={line ? line.id : "skeleton"}>
              <TableCellAvatar
                className={classes.colName}
                thumbnail={maybe(() => line.thumbnail.url)}
              >
                {maybe(() => line.productName && line.productSku) ? (
                  <>
                    <Typography variant="body2">{line.productName}</Typography>
                    <Typography variant="caption">{line.productSku}</Typography>
                  </>
                ) : (
                  <Skeleton />
                )}
              </TableCellAvatar>
              <TableCell className={classes.colQuantity}>
                {maybe(() => line.quantity) ? (
                  <Form
                    initial={{ quantity: line.quantity }}
                    onSubmit={data => onOrderLineChange(line.id, data)}
                  >
                    {({ change, data, hasChanged, submit }) => (
                      <DebounceForm
                        change={change}
                        submit={hasChanged ? submit : undefined}
                        time={200}
                      >
                        {debounce => (
                          <TextField
                            className={classes.quantityField}
                            fullWidth
                            name="quantity"
                            type="number"
                            value={data.quantity}
                            onChange={debounce}
                          />
                        )}
                      </DebounceForm>
                    )}
                  </Form>
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.colPrice}>
                {maybe(() => line.unitPrice.net) ? (
                  <Money money={line.unitPrice.net} />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.colTotal}>
                {maybe(() => line.unitPrice.net && line.quantity) ? (
                  <Money
                    money={{
                      amount: line.unitPrice.net.amount * line.quantity,
                      currency: line.unitPrice.net.currency
                    }}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell className={classes.colAction}>
                <IconButton onClick={() => onOrderLineRemove(line.id)}>
                  <DeleteIcon color="primary" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
);
OrderDraftDetailsProducts.displayName = "OrderDraftDetailsProducts";
export default OrderDraftDetailsProducts;
