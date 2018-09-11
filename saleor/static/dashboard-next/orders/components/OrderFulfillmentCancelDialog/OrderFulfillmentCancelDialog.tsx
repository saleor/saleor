import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../../i18n";

interface OrderFulfillmentCancelDialogProps {
  open: boolean;
  id: string;
  onClose?();
  onConfirm?();
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
>(({ classes, id, open, onConfirm, onClose }) => (
  <Dialog open={open}>
    <DialogTitle>
      {i18n.t("Cancel fulfillment", { context: "title" })}
    </DialogTitle>
    <DialogContent>
      <DialogContentText
        dangerouslySetInnerHTML={{
          __html: i18n.t(
            "Are you sure you want to cancel <strong>#{{ id }}</strong>?",
            { id }
          )
        }}
      />
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>{i18n.t("Back", { context: "button" })}</Button>
      <Button
        className={classes.deleteButton}
        variant="raised"
        onClick={onConfirm}
      >
        {i18n.t("Cancel fulfillment", { context: "button" })}
      </Button>
    </DialogActions>
  </Dialog>
));
export default OrderFulfillmentCancelDialog;
