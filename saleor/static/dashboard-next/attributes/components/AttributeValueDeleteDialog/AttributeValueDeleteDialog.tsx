import DialogContentText from "@material-ui/core/DialogContentText";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "@saleor/i18n";

export interface AttributeValueDeleteDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  onConfirm: () => void;
  onClose: () => void;
  name: string;
}

const AttributeValueDeleteDialog: React.FC<AttributeValueDeleteDialogProps> = ({
  name,
  confirmButtonState,
  onClose,
  onConfirm,
  open
}) => (
  <ActionDialog
    open={open}
    onClose={onClose}
    confirmButtonState={confirmButtonState}
    onConfirm={onConfirm}
    variant="delete"
    title={i18n.t("Remove attribute value")}
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to remove <strong>{{ name }}</strong>?",
          {
            name
          }
        )
      }}
    />
  </ActionDialog>
);

AttributeValueDeleteDialog.displayName = "AttributeValueDeleteDialog";
export default AttributeValueDeleteDialog;
