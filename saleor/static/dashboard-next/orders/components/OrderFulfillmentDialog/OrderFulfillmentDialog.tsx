import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
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
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton/ConfirmButton";
import Form from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderDetails_order_lines } from "../../types/OrderDetails";

export interface FormData {
  lines: number[];
  trackingNumber: string;
}

const styles = (theme: Theme) =>
  createStyles({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit * 3,
      width: theme.spacing.unit * 5
    },
    quantityInput: {
      width: "4rem"
    },
    quantityInputContainer: {
      paddingRight: theme.spacing.unit,
      textAlign: "right" as "right"
    },
    remainingQuantity: {
      paddingBottom: 4
    },
    textRight: {
      textAlign: "right" as "right"
    }
  });

export interface OrderFulfillmentDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  lines: OrderDetails_order_lines[];
  onClose();
  onSubmit(data: FormData);
}

const OrderFulfillmentDialog = withStyles(styles, {
  name: "OrderFulfillmentDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    lines,
    onClose,
    onSubmit
  }: OrderFulfillmentDialogProps) => (
    <Dialog open={open}>
      <Form
        initial={{
          lines: maybe(
            () =>
              lines.map(
                product => product.quantity - product.quantityFulfilled
              ),
            []
          ),
          trackingNumber: ""
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
                    <TableCell className={classes.textRight} colSpan={2}>
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
                        <TableCell className={classes.quantityInputContainer}>
                          <TextField
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
                          />
                        </TableCell>
                        <TableCell>
                          <div className={classes.remainingQuantity}>
                            / {remainingQuantity}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              <DialogContent>
                <FormSpacer />
                <TextField
                  fullWidth
                  label={i18n.t("Tracking number")}
                  name="trackingNumber"
                  value={data.trackingNumber}
                  onChange={change}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <ConfirmButton
                  transitionState={confirmButtonState}
                  color="primary"
                  variant="contained"
                  type="submit"
                >
                  {i18n.t("Confirm", { context: "button" })}
                </ConfirmButton>
              </DialogActions>
            </>
          );
        }}
      </Form>
    </Dialog>
  )
);
OrderFulfillmentDialog.displayName = "OrderFulfillmentDialog";
export default OrderFulfillmentDialog;
