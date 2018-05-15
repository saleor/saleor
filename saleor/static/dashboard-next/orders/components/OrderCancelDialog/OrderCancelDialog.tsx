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

interface OrderCancelDialogProps {
  open: boolean;
  id: string;
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(theme => ({
  deleteButton: {
    "&:hover": {
      backgroundColor: theme.palette.error.main
    },
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText
  }
}));
const OrderCancelDialog = decorate<OrderCancelDialogProps>(
  ({ children, classes, id, open, onConfirm, onClose }) => (
    <Dialog open={open}>
      <DialogTitle>{i18n.t("Cancel order", { context: "title" })}</DialogTitle>
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
        <Button onClick={onClose}>
          {i18n.t("Back", { context: "button" })}
        </Button>
        <Button
          className={classes.deleteButton}
          variant="raised"
          onClick={onConfirm}
        >
          {i18n.t("Cancel order", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  )
);
export default OrderCancelDialog;
