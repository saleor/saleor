import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import i18n from "../../../i18n";

export interface OrderDraftFinalizeDialogProps {
  open: boolean;
  orderNumber: string;
  onClose: () => void;
  onConfirm: () => void;
}

const OrderDraftFinalizeDialog: React.StatelessComponent<
  OrderDraftFinalizeDialogProps
> = ({ open, onClose, onConfirm, orderNumber }) => (
  <ActionDialog
    onClose={onClose}
    onConfirm={onConfirm}
    open={open}
    title={i18n.t("Finalize draft order", {
      context: "modal title"
    })}
  >
    <DialogContentText
      dangerouslySetInnerHTML={{
        __html: i18n.t(
          "Are you sure you want to finalize draft <strong>#{{ number }}</strong>?",
          {
            context: "modal",
            number: orderNumber
          }
        )
      }}
    />
  </ActionDialog>
);
OrderDraftFinalizeDialog.displayName = "OrderDraftFinalize";
export default OrderDraftFinalizeDialog;
