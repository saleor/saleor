import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "@saleor/i18n";

export interface AttributeDeleteDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  onConfirm: () => void;
  onClose: () => void;
  name: string;
}

const AttributeDeleteDialog: React.FC<AttributeDeleteDialogProps> = ({
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
    title={i18n.t("Remove attribute")}
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

AttributeDeleteDialog.displayName = "AttributeDeleteDialog";
export default AttributeDeleteDialog;
