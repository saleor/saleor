import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle
} from "material-ui/Dialog";
import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import * as React from "react";

import i18n from "../../../i18n";

interface OrderPaymentDialogProps {
  open: boolean;
  value: number;
  variant: string;
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(theme => ({ root: {} }));
const OrderPaymentDialog = decorate<OrderPaymentDialogProps>(
  ({ children, classes, open, variant, onConfirm, onClose, onChange }) => (
    <Dialog open={open}>
      <DialogTitle>
        {variant === "capture"
          ? i18n.t("Capture payment", { context: "title" })
          : i18n.t("Refund payment", { context: "title" })}
      </DialogTitle>
      <DialogContent>
        <TextField
          label={i18n.t("Amount")}
          name="value"
          onChange={onChange}
          fullWidth
          type="number"
        />
      </DialogContent>
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
export default OrderPaymentDialog;
