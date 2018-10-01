import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogTitle from "@material-ui/core/DialogTitle";
import Input from "@material-ui/core/Input";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Form from "../../../components/Form";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderDetails_order_lines_edges_node } from "../../types/OrderDetails";

export interface FormData {
  lines: number[];
}

export interface OrderFulfillmentDialogProps {
  open: boolean;
  lines: OrderDetails_order_lines_edges_node[];
  onClose();
  onSubmit(data: FormData);
}

const decorate = withStyles(
  theme => ({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit * 3,
      width: theme.spacing.unit * 5
    },
    quantityInput: {
      width: "4rem"
    },
    textRight: {
      textAlign: "right" as "right"
    }
  }),
  { name: "OrderFulfillmentDialog" }
);
const OrderFulfillmentDialog = decorate<OrderFulfillmentDialogProps>(
  ({ classes, open, lines, onClose, onSubmit }) => (
    <Dialog open={open}>
      <Form
        initial={{
          lines: maybe(
            () =>
              lines.map(
                product => product.quantity - product.quantityFulfilled
              ),
            []
          )
        }}
        onSubmit={onSubmit}
      >
        {({ data, change }) => {
          const handleQuantityChange = (
            productIndex: number,
            event: React.ChangeEvent<any>
          ) => {
            const newData = data.lines;
            newData[productIndex] = event.target.value;
            change({
              target: {
                name: "lines",
                value: newData
              }
            } as any);
          };
          return (
            <>
              <DialogTitle>{i18n.t("Fulfill products")}</DialogTitle>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell />
                    <TableCell>{i18n.t("Product name")}</TableCell>
                    <TableCell>{i18n.t("SKU")}</TableCell>
                    <TableCell className={classes.textRight}>
                      {i18n.t("Quantity")}
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {lines.map((product, productIndex) => {
                    const remainingQuantity =
                      product.quantity - product.quantityFulfilled;
                    return (
                      <TableRow key={product.id}>
                        <TableCellAvatar thumbnail={product.thumbnailUrl} />
                        <TableCell>{product.productName}</TableCell>
                        <TableCell>{product.productSku}</TableCell>
                        <TableCell className={classes.textRight}>
                          <Input
                            type="number"
                            inputProps={{
                              max: remainingQuantity,
                              style: { textAlign: "right" }
                            }}
                            className={classes.quantityInput}
                            value={data.lines[productIndex]}
                            onChange={event =>
                              handleQuantityChange(productIndex, event)
                            }
                            error={remainingQuantity < data.lines[productIndex]}
                          />{" "}
                          / {remainingQuantity}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <Button color="primary" variant="raised" type="submit">
                  {i18n.t("Confirm", { context: "button" })}
                </Button>
              </DialogActions>
            </>
          );
        }}
      </Form>
    </Dialog>
  )
);
export default OrderFulfillmentDialog;
