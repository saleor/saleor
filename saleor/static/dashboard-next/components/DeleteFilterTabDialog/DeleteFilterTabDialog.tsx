import DialogContentText from "@material-ui/core/DialogContentText";
import React from "react";

import i18n from "../../i18n";
import ActionDialog from "../ActionDialog";
import { ConfirmButtonTransitionState } from "../ConfirmButton";

export interface DeleteFilterTabDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  tabName: string;
  onClose: () => void;
  onSubmit: () => void;
}

const DeleteFilterTabDialog: React.FC<DeleteFilterTabDialogProps> = ({
  confirmButtonState,
  onClose,
  onSubmit,
  open,
  tabName
}) => (
  <ActionDialog
    open={open}
    confirmButtonState={confirmButtonState}
    onClose={onClose}
    onConfirm={onSubmit}
    title={i18n.t("Delete Search", {
      context: "modal title custom search delete"
    })}
    variant="delete"
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to delete <strong>{{ name }}</strong> search tab?",
          {
            name: tabName
          }
        )
      }}
    />
  </ActionDialog>
);
DeleteFilterTabDialog.displayName = "DeleteFilterTabDialog";
export default DeleteFilterTabDialog;
