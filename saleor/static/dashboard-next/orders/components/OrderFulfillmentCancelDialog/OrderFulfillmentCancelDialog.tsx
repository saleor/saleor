import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import Form from "../../../components/Form";
import i18n from "../../../i18n";

export interface FormData {
  restock: boolean;
}

interface OrderFulfillmentCancelDialogProps {
  open: boolean;
  onClose();
  onConfirm(data: FormData);
}

const decorate = withStyles(
  theme => ({
    deleteButton: {
      "&:hover": {
        backgroundColor: theme.palette.error.main
      },
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    }
  }),
  { name: "OrderFulfillmentCancelDialog" }
);
const OrderFulfillmentCancelDialog = decorate<
  OrderFulfillmentCancelDialogProps
>(({ classes, open, onConfirm, onClose }) => (
  <Dialog open={open}>
    <Form initial={{ restock: true }} onSubmit={onConfirm}>
      {({ change, data, submit }) => (
        <>
          <DialogTitle>
            {i18n.t("Cancel fulfillment", { context: "title" })}
          </DialogTitle>
          <DialogContent>
            <DialogContentText>
              {i18n.t("Are you sure you want to cancel this fulfillment?")}
            </DialogContentText>
            <ControlledCheckbox
              checked={data.restock}
              label={i18n.t("Restock items?")}
              name="restock"
              onChange={change}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>
              {i18n.t("Back", { context: "button" })}
            </Button>
            <Button
              className={classes.deleteButton}
              variant="raised"
              onClick={submit}
            >
              {i18n.t("Cancel fulfillment", { context: "button" })}
            </Button>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
));
export default OrderFulfillmentCancelDialog;
