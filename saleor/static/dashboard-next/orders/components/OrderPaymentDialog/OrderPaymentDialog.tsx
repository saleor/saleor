import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
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

const OrderPaymentDialog: React.StatelessComponent<OrderPaymentDialogProps> = ({
  open,
  variant,
  onConfirm,
  onClose,
  onChange
}) => (
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
);
export default OrderPaymentDialog;
