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

export interface MenuCreateDialogFormData {
  name: string;
}

export interface MenuCreateDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  open: boolean;
  onClose: () => void;
  onConfirm: (data: MenuCreateDialogFormData) => void;
}

const initialForm: MenuCreateDialogFormData = {
  name: ""
};

const MenuCreateDialog: React.FC<MenuCreateDialogProps> = ({
  confirmButtonState,
  disabled,
  onClose,
  onConfirm,
  open
}) => (
  <Dialog maxWidth="sm" fullWidth open={open}>
    <DialogTitle>
      {i18n.t("Add Menu", {
        context: "create menu modal window title"
      })}
    </DialogTitle>
    <Form initial={initialForm} onSubmit={onConfirm}>
      {({ change, data, errors: formErrors, submit }) => (
        <>
          <DialogContent>
            <TextField
              disabled={disabled}
              error={!!formErrors.name}
              fullWidth
              helperText={formErrors.name}
              label={i18n.t("Menu Title")}
              name={"name" as keyof MenuCreateDialogFormData}
              value={data.name}
              onChange={change}
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
              onClick={submit}
            >
              {i18n.t("Create")}
            </ConfirmButton>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
);

MenuCreateDialog.displayName = "MenuCreateDialog";
export default MenuCreateDialog;
