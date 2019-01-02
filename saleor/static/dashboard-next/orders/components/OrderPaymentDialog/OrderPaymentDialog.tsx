import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import i18n from "../../../i18n";

export interface FormData {
  amount: number;
}

interface OrderPaymentDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  initial: number;
  variant: string;
  onClose: () => void;
  onSubmit: (data: FormData) => void;
}

const OrderPaymentDialog: React.StatelessComponent<OrderPaymentDialogProps> = ({
  confirmButtonState,
  open,
  initial,
  variant,
  onClose,
  onSubmit
}) => (
  <Dialog open={open}>
    <Form
      initial={{
        amount: initial
      }}
      onSubmit={data => {
        onSubmit(data);
        onClose();
      }}
    >
      {({ data, change, submit }) => (
        <>
          <DialogTitle>
            {variant === "capture"
              ? i18n.t("Capture payment", { context: "title" })
              : i18n.t("Refund payment", { context: "title" })}
          </DialogTitle>

          <DialogContent>
            <TextField
              fullWidth
              label={i18n.t("Amount")}
              name="amount"
              onChange={change}
              inputProps={{
                step: "0.01"
              }}
              type="number"
              value={data.amount}
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
              onClick={data => {
                onClose();
                submit(data);
              }}
            >
              {i18n.t("Confirm", { context: "button" })}
            </ConfirmButton>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
);
OrderPaymentDialog.displayName = "OrderPaymentDialog";
export default OrderPaymentDialog;
