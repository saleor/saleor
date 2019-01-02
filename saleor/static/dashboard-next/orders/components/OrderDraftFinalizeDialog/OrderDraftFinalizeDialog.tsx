import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import i18n from "../../../i18n";

export type OrderDraftFinalizeWarning =
  | "no-shipping"
  | "no-billing"
  | "no-user"
  | "no-shipping-method"
  | "unnecessary-shipping-method";

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
    case "unnecessary-shipping-method":
      return i18n.t("Shipping method provided, but no product requires it");
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
    confirmButtonLabel={
      warnings.length > 0 ? i18n.t("Finalize anyway") : i18n.t("Finalize")
    }
    confirmButtonState={confirmButtonState}
    variant={warnings.length > 0 ? "delete" : "default"}
  >
    <DialogContentText component="div">
      {warnings.length > 0 && (
        <>
          <p>
            {i18n.t(
              "There are missing or incorrect informations about this order:"
            )}
          </p>
          <ul>
            {warnings.map(warning => (
              <li key={warning}>{warningToText(warning)}</li>
            ))}
          </ul>
        </>
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
