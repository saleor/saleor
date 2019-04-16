import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import ControlledCheckbox from "../../../components/ControlledCheckbox";
import i18n from "../../../i18n";

export interface OrderBulkCancelDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  numberOfOrders: string;
  open: boolean;
  onClose: () => void;
  onConfirm: (restock: boolean) => void;
}

const OrderBulkCancelDialog: React.StatelessComponent<
  OrderBulkCancelDialogProps
> = ({ confirmButtonState, numberOfOrders, open, onClose, onConfirm }) => {
  const [restock, setRestock] = React.useState(true);

  return (
    <ActionDialog
      confirmButtonState={confirmButtonState}
      open={open}
      variant="delete"
      title={i18n.t("Cancel Orders")}
      onClose={onClose}
      onConfirm={() => onConfirm(restock)}
    >
      <DialogContentText
        dangerouslySetInnerHTML={{
          __html: i18n.t(
            "Are you sure you want to cancel <strong>{{ number }}</strong> orders?",
            {
              number: numberOfOrders
            }
          )
        }}
      />
      <ControlledCheckbox
        checked={restock}
        label={i18n.t("Release all stock allocated to these orders")}
        name="restock"
        onChange={event => setRestock(event.target.value)}
      />
    </ActionDialog>
  );
};
OrderBulkCancelDialog.displayName = "OrderBulkCancelDialog";
export default OrderBulkCancelDialog;
