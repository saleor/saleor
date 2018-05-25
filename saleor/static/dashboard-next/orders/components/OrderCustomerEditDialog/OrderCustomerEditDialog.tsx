import Button from "material-ui/Button";
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogProps,
  DialogTitle
} from "material-ui/Dialog";
import { InputAdornment } from "material-ui/Input";
import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import Typography from "material-ui/Typography";
import * as React from "react";

import { SingleAutocompleteSelectField } from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

interface OrderCustomerEditDialogProps {
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

const decorate = withStyles(theme => ({
  dialog: {
    overflowY: "visible" as "visible"
  },
  select: {
    flex: 1,
    marginRight: theme.spacing.unit * 2
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "1fr 6rem",
    overflowY: "visible" as "visible",
    width: theme.breakpoints.values.sm
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const OrderCustomerEditDialog = decorate<OrderCustomerEditDialogProps>(
  ({
    classes,
    open,
    loading,
    user,
    users,
    fetchUsers,
    onChange,
    onClose,
    onConfirm
  }) => {
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
            name="user"
            value={user}
            choices={choices}
            onChange={onChange}
            fetchChoices={fetchUsers}
            loading={loading}
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
    );
  }
);
export default OrderCustomerEditDialog;
