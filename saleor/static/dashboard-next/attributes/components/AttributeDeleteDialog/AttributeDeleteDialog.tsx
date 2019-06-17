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
  attributeName: string;
}

const AttributeDeleteDialog: React.FC<AttributeDeleteDialogProps> = () => (
  <ActionDialog
    open={params.action === "remove"}
    onClose={() => navigate(productUrl(id), true)}
    confirmButtonState={deleteTransitionState}
    onConfirm={() => deleteProduct.mutate({ id })}
    variant="delete"
    title={i18n.t("Remove product")}
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to remove <strong>{{ name }}</strong>?",
          {
            name: product ? product.name : undefined
          }
        )
      }}
    />
  </ActionDialog>
);

AttributeDeleteDialog.displayName = "AttributeDeleteDialog";
export default AttributeDeleteDialog;
