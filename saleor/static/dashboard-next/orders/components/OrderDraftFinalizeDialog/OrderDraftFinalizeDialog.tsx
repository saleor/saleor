import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import i18n from "../../../i18n";

export type OrderDraftFinalizeWarning =
  | "no-shipping"
  | "no-billing"
  | "no-user"
  | "no-shipping-method";

export interface OrderDraftFinalizeDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  orderNumber: string;
  warnings: OrderDraftFinalizeWarning[];
  onClose: () => void;
  onConfirm: () => void;
}

const warningToText = (warning: OrderDraftFinalizeWarning) => {
  switch (warning) {
    case "no-shipping":
      return i18n.t("No shipping address");
    case "no-billing":
      return i18n.t("No billing address");
    case "no-user":
      return i18n.t("No user information");
    case "no-shipping-method":
      return i18n.t("Some products require shipping, but no method provided");
  }
};

const OrderDraftFinalizeDialog: React.StatelessComponent<
  OrderDraftFinalizeDialogProps
> = ({
  confirmButtonState,
  open,
  warnings,
  onClose,
  onConfirm,
  orderNumber
}) => (
  <ActionDialog
    onClose={onClose}
    onConfirm={onConfirm}
    open={open}
    title={i18n.t("Finalize draft order", {
      context: "modal title"
    })}
    confirmButtonState={confirmButtonState}
  >
    <DialogContentText>
      {warnings.length > 0 && (
        <p>
          {i18n.t("There are missing informations about this order.")}
          <ul>
            {warnings.map(warning => (
              <li>{warningToText(warning)}</li>
            ))}
          </ul>
        </p>
      )}
      <span
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
    </DialogContentText>
  </ActionDialog>
);
OrderDraftFinalizeDialog.displayName = "OrderDraftFinalize";
export default OrderDraftFinalizeDialog;
