import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "@saleor/i18n";

export interface ProductTypeDeleteDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  name: string;
  onClose: () => void;
  onConfirm: () => void;
}

const ProductTypeDeleteDialog: React.FC<ProductTypeDeleteDialogProps> = ({
  confirmButtonState,
  open,
  name,
  onClose,
  onConfirm
}) => (
  <ActionDialog
    confirmButtonState={confirmButtonState}
    open={open}
    onClose={onClose}
    onConfirm={onConfirm}
    title={i18n.t("Remove product type")}
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
ProductTypeDeleteDialog.displayName = "ProductTypeDeleteDialog";
export default ProductTypeDeleteDialog;
