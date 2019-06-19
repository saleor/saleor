import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "../../../i18n";

export interface AttributeBulkDeleteDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  quantity: string;
  open: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

const AttributeBulkDeleteDialog: React.StatelessComponent<
  AttributeBulkDeleteDialogProps
> = ({ confirmButtonState, quantity, onClose, onConfirm, open }) => (
  <ActionDialog
    open={open}
    confirmButtonState={confirmButtonState}
    onClose={onClose}
    onConfirm={onConfirm}
    title={i18n.t("Remove attributes")}
    variant="delete"
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to remove <strong>{{ quantity }}</strong> attributes?",
          {
            quantity
          }
        )
      }}
    />
  </ActionDialog>
);
AttributeBulkDeleteDialog.displayName = "AttributeBulkDeleteDialog";
export default AttributeBulkDeleteDialog;
