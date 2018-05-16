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

interface OrderFulfillmentTrackingDialogProps {
  open: boolean;
  trackingCode: string;
  variant: string;
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?();
}

const decorate = withStyles(theme => ({}));
const OrderFulfillmentTrackingDialog = decorate<
  OrderFulfillmentTrackingDialogProps
>(
  ({
    children,
    classes,
    open,
    variant,
    trackingCode,
    onConfirm,
    onClose,
    onChange
  }) => (
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
  )
);
export default OrderFulfillmentTrackingDialog;
