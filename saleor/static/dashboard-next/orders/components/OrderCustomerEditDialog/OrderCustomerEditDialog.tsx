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
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton/ConfirmButton";
import { SingleAutocompleteSelectField } from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    dialog: {
      overflowY: "visible"
    },
    root: {
      overflowY: "visible",
      width: theme.breakpoints.values.sm
    },
    select: {
      flex: 1,
      marginRight: theme.spacing.unit * 2
    },
    textRight: {
      textAlign: "right"
    }
  });

interface OrderCustomerEditDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  user?: {
    label: string;
    value: string;
  };
  users?: Array<{
    id: string;
    email: string;
  }>;
  loading?: boolean;
  fetchUsers(value: string);
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const OrderCustomerEditDialog = withStyles(styles, {
  name: "OrderCustomerEditDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    loading,
    user,
    users,
    fetchUsers,
    onChange,
    onClose,
    onConfirm
  }: OrderCustomerEditDialogProps) => {
    const choices =
      !loading && users
        ? users.map(v => ({
            label: v.email,
            value: v.id
          }))
        : [];
    return (
      <Dialog open={open} classes={{ paper: classes.dialog }}>
        <DialogTitle>{i18n.t("Edit customer details")}</DialogTitle>
        <DialogContent className={classes.root}>
          <SingleAutocompleteSelectField
            choices={choices}
            custom
            loading={loading}
            name="user"
            value={user}
            fetchChoices={fetchUsers}
            onChange={onChange}
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
            onClick={onConfirm}
          >
            {i18n.t("Confirm", { context: "button" })}
          </ConfirmButton>
        </DialogActions>
      </Dialog>
    );
  }
);
OrderCustomerEditDialog.displayName = "OrderCustomerEditDialog";
export default OrderCustomerEditDialog;
