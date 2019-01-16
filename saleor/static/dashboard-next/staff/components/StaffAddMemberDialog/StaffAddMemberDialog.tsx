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
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton/ConfirmButton";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import Form from "../../../components/Form";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { UserError } from "../../../types";

export interface FormData {
  email: string;
  firstName: string;
  fullAccess: boolean;
  lastName: string;
}

const initialForm: FormData = {
  email: "",
  firstName: "",
  fullAccess: false,
  lastName: ""
};

const styles = (theme: Theme) =>
  createStyles({
    hr: {
      backgroundColor: "#eaeaea",
      border: "none",
      height: 1,
      marginBottom: 0
    },
    sectionTitle: {
      fontWeight: 600 as 600,
      marginBottom: theme.spacing.unit,
      marginTop: theme.spacing.unit * 2
    },
    textFieldGrid: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface StaffAddMemberDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  errors: UserError[];
  open: boolean;
  onClose: () => void;
  onConfirm: (data: FormData) => void;
}

const StaffAddMemberDialog = withStyles(styles, {
  name: "StaffAddMemberDialog"
})(
  ({
    classes,
    confirmButtonState,
    errors,
    open,
    onClose,
    onConfirm
  }: StaffAddMemberDialogProps) => (
    <Dialog open={open}>
      <Form errors={errors} initial={initialForm} onSubmit={onConfirm}>
        {({ change, data, errors: formErrors, hasChanged }) => (
          <>
            <DialogTitle>{i18n.t("Add Staff Member")}</DialogTitle>
            <DialogContent>
              <div className={classes.textFieldGrid}>
                <TextField
                  error={!!formErrors.firstName}
                  helperText={formErrors.firstName}
                  label={i18n.t("First Name")}
                  name="firstName"
                  type="text"
                  value={data.firstName}
                  onChange={change}
                />
                <TextField
                  error={!!formErrors.lastName}
                  helperText={formErrors.lastName}
                  label={i18n.t("Last Name")}
                  name="lastName"
                  type="text"
                  value={data.lastName}
                  onChange={change}
                />
              </div>
              <FormSpacer />
              <TextField
                error={!!formErrors.email}
                fullWidth
                helperText={formErrors.email}
                label={i18n.t("Email address")}
                name="email"
                type="email"
                value={data.email}
                onChange={change}
              />
            </DialogContent>
            <hr className={classes.hr} />
            <DialogContent>
              <Typography className={classes.sectionTitle}>
                {i18n.t("Permissions")}
              </Typography>
              <Typography>
                {i18n.t(
                  "Expand or restrict user’s permissions to access certain part of saleor system."
                )}
              </Typography>
              <ControlledCheckbox
                checked={data.fullAccess}
                label={i18n.t("User has full access")}
                name="fullAccess"
                onChange={change}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={onClose}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
              <ConfirmButton
                color="primary"
                disabled={!hasChanged}
                variant="contained"
                type="submit"
                transitionState={confirmButtonState}
              >
                {i18n.t("Send invite", { context: "button" })}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
StaffAddMemberDialog.displayName = "StaffAddMemberDialog";
export default StaffAddMemberDialog;
