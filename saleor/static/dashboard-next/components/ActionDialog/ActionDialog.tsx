import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../ConfirmButton/ConfirmButton";

const styles = (theme: Theme) =>
  createStyles({
    deleteButton: {
      "&:hover": {
        backgroundColor: theme.palette.error.main
      },
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    }
  });

interface ActionDialogProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  confirmButtonLabel?: string;
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  title: string;
  variant?: "default" | "delete";
  onClose?();
  onConfirm();
}

const ActionDialog = withStyles(styles, { name: "ActionDialog" })(
  ({
    children,
    classes,
    confirmButtonLabel,
    confirmButtonState,
    open,
    title,
    variant,
    onConfirm,
    onClose
  }: ActionDialogProps) => (
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
          variant="contained"
          onClick={onConfirm}
          className={classNames({
            [classes.deleteButton]: variant === "delete"
          })}
        >
          {confirmButtonLabel ||
            (variant === "delete"
              ? i18n.t("Delete", { context: "button" })
              : i18n.t("Confirm", { context: "button" }))}
        </ConfirmButton>
      </DialogActions>
    </Dialog>
  )
);
ActionDialog.displayName = "ActionDialog";
export default ActionDialog;
