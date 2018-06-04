import Avatar from "material-ui/Avatar";
import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle
} from "material-ui/Dialog";
import Input from "material-ui/Input";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from "material-ui/Table";
import TextField from "material-ui/TextField";
import * as React from "react";

import i18n from "../../../i18n";

interface OrderFulfillmentDialogProps {
  open: boolean;
  products?: Array<{
    id: string;
    name: string;
    sku: string;
    quantity: number;
    thumbnailUrl: string;
  }>;
  data: any;
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(theme => ({
  avatarCell: {
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 3,
    width: theme.spacing.unit * 5
  },
  textRight: {
    textAlign: "right" as "right"
  },
  quantityInput: {
    width: "4rem"
  },
  root: {}
}));
const OrderFulfillmentDialog = decorate<OrderFulfillmentDialogProps>(
  ({ classes, open, products, data, onChange, onClose, onConfirm }) => (
    <Dialog open={open}>
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
          {products.map(product => (
            <TableRow>
              <TableCell className={classes.avatarCell}>
                <Avatar src={product.thumbnailUrl} />
              </TableCell>
              <TableCell>{product.name}</TableCell>
              <TableCell>{product.sku}</TableCell>
              <TableCell className={classes.textRight}>
                <Input
                  type="number"
                  inputProps={{
                    max: product.quantity,
                    style: { textAlign: "right" }
                  }}
                  className={classes.quantityInput}
                  value={data[product.id]}
                  onChange={onChange}
                  name={product.id}
                  error={product.quantity < data[product.id]}
                />{" "}
                / {product.quantity}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {i18n.t("Confirm", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  )
);
export default OrderFulfillmentDialog;
