import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import Form from "@saleor/components/Form";
import i18n from "../../../i18n";

export interface FormData {
  trackingNumber: string;
}

interface OrderFulfillmentTrackingDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  trackingNumber: string;
  onClose();
  onConfirm(data: FormData);
}

const OrderFulfillmentTrackingDialog: React.StatelessComponent<
  OrderFulfillmentTrackingDialogProps
> = ({ confirmButtonState, open, trackingNumber, onConfirm, onClose }) => (
  <Dialog onClose={onClose} open={open}>
    <Form initial={{ trackingNumber }} onSubmit={onConfirm}>
      {({ change, data, submit }) => (
        <>
          <DialogTitle>
            {i18n.t("Add tracking code", { context: "title" })}
          </DialogTitle>
          <DialogContent>
            <TextField
              label={i18n.t("Tracking number")}
              name="trackingNumber"
              onChange={change}
              value={data.trackingNumber}
              fullWidth
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
              onClick={submit}
            >
              {i18n.t("Confirm", { context: "button" })}
            </ConfirmButton>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
);
OrderFulfillmentTrackingDialog.displayName = "OrderFulfillmentTrackingDialog";
export default OrderFulfillmentTrackingDialog;
