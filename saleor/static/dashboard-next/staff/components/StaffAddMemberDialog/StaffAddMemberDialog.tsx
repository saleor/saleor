import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import Form from "../../../components/Form";
import i18n from "../../../i18n";
import { UserError } from "../../../types";

export interface FormData {
  email: string;
  fullAccess: boolean;
}
interface StaffAddMemberDialogProps {
  errors: UserError[];
  open: boolean;
  onClose: () => void;
  onConfirm: (data: FormData) => void;
}

const initialForm: FormData = {
  email: "",
  fullAccess: false
};

const decorate = withStyles(theme => ({
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
  }
}));
const StaffAddMemberDialog = decorate<StaffAddMemberDialogProps>(
  ({ classes, errors, open, onClose, onConfirm }) => (
    <Dialog open={open}>
      <Form errors={errors} initial={initialForm} onSubmit={onConfirm}>
        {({ change, data, errors: formErrors, hasChanged }) => (
          <>
            <DialogTitle>{i18n.t("Add Staff Member")}</DialogTitle>
            <DialogContent>
              <TextField
                error={!!formErrors.email}
                fullWidth
                helperText={formErrors.email}
                label={i18n.t("E-mail")}
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
              <Button
                color="primary"
                disabled={!hasChanged}
                variant="raised"
                type="submit"
              >
                {i18n.t("Send invite", { context: "button" })}
              </Button>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  )
);
StaffAddMemberDialog.displayName = "StaffAddMemberDialog";
export default StaffAddMemberDialog;
