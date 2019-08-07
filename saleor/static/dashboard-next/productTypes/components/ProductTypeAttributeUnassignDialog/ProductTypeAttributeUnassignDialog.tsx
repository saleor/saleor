import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import i18n from "@saleor/i18n";

export interface ProductTypeAttributeUnassignDialogProps {
  attributeName: string;
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  productTypeName: string;
  onClose: () => void;
  onConfirm: () => void;
}

const ProductTypeAttributeUnassignDialog: React.FC<
  ProductTypeAttributeUnassignDialogProps
> = ({
  attributeName,
  confirmButtonState,
  open,
  productTypeName,
  onClose,
  onConfirm
}) => (
  <ActionDialog
    confirmButtonState={confirmButtonState}
    open={open}
    onClose={onClose}
    onConfirm={onConfirm}
    title={i18n.t("Unassign attribute from product type")}
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to unassign <strong>{{ attributeName }}</strong> from <strong>{{ productTypeName }}</strong>?",
          {
            attributeName,
            productTypeName
          }
        )
      }}
    />
  </ActionDialog>
);
ProductTypeAttributeUnassignDialog.displayName =
  "ProductTypeAttributeUnassignDialog";
export default ProductTypeAttributeUnassignDialog;
