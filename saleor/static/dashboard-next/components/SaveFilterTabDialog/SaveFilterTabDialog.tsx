import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import i18n from "../../i18n";
import ConfirmButton, { ConfirmButtonTransitionState } from "../ConfirmButton";
import Form from "../Form";

export interface SaveFilterTabDialogFormData {
  name: string;
}

const initialForm: SaveFilterTabDialogFormData = {
  name: ""
};

export interface SaveFilterTabDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  onClose: () => void;
  onSubmit: (data: SaveFilterTabDialogFormData) => void;
}

const SaveFilterTabDialog: React.FC<SaveFilterTabDialogProps> = ({
  confirmButtonState,
  onClose,
  onSubmit,
  open
}) => (
  <Dialog open={open} fullWidth maxWidth="sm">
    <DialogTitle>
      {i18n.t("Save Custom Search", {
        context: "save filter tab"
      })}
    </DialogTitle>
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, submit }) => (
        <>
          <DialogContent>
            <TextField
              fullWidth
              label={i18n.t("Search Name", {
                context: "save search"
              })}
              name={"name" as keyof SaveFilterTabDialogFormData}
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
              {i18n.t("Save")}
            </ConfirmButton>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
);
SaveFilterTabDialog.displayName = "SaveFilterTabDialog";
export default SaveFilterTabDialog;
