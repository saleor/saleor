import DialogContentText from "@material-ui/core/DialogContentText";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "@saleor/i18n";

export interface AttributeValueDeleteDialogProps {
  attributeName: string;
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  name: string;
  useName?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

const AttributeValueDeleteDialog: React.FC<AttributeValueDeleteDialogProps> = ({
  attributeName,
  name,
  confirmButtonState,
  useName,
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
    <DialogContentText>
      {useName
        ? i18n.t(
            'Are you sure you want to remove "{{ name }}" value? If you remove it you won’t be able to assign it to any of the products with "{{ attributeName }}" attribute.',
            {
              attributeName,
              name
            }
          )
        : i18n.t('Are you sure you want to remove "{{ name }}" value?', {
            name
          })}
    </DialogContentText>
  </ActionDialog>
);

AttributeValueDeleteDialog.displayName = "AttributeValueDeleteDialog";
export default AttributeValueDeleteDialog;
