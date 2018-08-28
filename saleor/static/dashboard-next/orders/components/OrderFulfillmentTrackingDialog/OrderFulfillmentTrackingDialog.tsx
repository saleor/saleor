import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import i18n from "../../../i18n";

interface OrderFulfillmentTrackingDialogProps {
  open: boolean;
  trackingCode: string;
  variant: string;
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?();
}

const OrderFulfillmentTrackingDialog: React.StatelessComponent<
  OrderFulfillmentTrackingDialogProps
> = ({ open, variant, trackingCode, onConfirm, onClose, onChange }) => (
  <Dialog open={open}>
    <DialogTitle>
      {variant === "edit"
        ? i18n.t("Edit tracking code", { context: "title" })
        : i18n.t("Add tracking code", { context: "title" })}
    </DialogTitle>
    <DialogContent>
      <TextField
        label={i18n.t("Tracking code")}
        name="trackingCode"
        onChange={onChange}
        value={trackingCode}
        fullWidth
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
export default OrderFulfillmentTrackingDialog;
