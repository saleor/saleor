import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle
} from "material-ui/Dialog";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import i18n from "../../../i18n";

interface OrderPaymentReleaseDialogProps {
  open: boolean;
  onClose?();
  onConfirm?();
}

const decorate = withStyles(theme => ({ root: {} }));
const OrderPaymentReleaseDialog = decorate<OrderPaymentReleaseDialogProps>(
  ({ children, classes, open, onConfirm, onClose }) => (
    <Dialog open={open}>
      <DialogTitle>
        {i18n.t("Release payment", { context: "title" })}
      </DialogTitle>
      <DialogContent>
        <DialogContentText>
          {i18n.t("Are you sure you want to release this payment?")}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Back", { context: "button" })}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {i18n.t("Confirm", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  )
);
export default OrderPaymentReleaseDialog;
