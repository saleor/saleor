import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../ConfirmButton/ConfirmButton";

interface ActionDialogProps {
  confirmButtonState?: ConfirmButtonTransitionState;
  open: boolean;
  title: string;
  variant?: string;
  onClose?();
  onConfirm();
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
const ActionDialog = decorate<ActionDialogProps>(
  ({
    children,
    classes,
    confirmButtonState,
    open,
    title,
    variant,
    onConfirm,
    onClose
  }) => (
    <Dialog open={open}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <ConfirmButton
          transitionState={confirmButtonState}
          color="primary"
          variant="raised"
          onClick={onConfirm}
          className={classNames({
            [classes.deleteButton]: variant === "delete"
          })}
        >
          {variant === "delete"
            ? i18n.t("Delete", { context: "button" })
            : i18n.t("Confirm", { context: "button" })}
        </ConfirmButton>
      </DialogActions>
    </Dialog>
  )
);
ActionDialog.displayName = "ActionDialog";
export default ActionDialog;
