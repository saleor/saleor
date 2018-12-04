import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit/AddressEdit";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton/ConfirmButton";
import Form from "../../../components/Form";
import { AddressTypeInput } from "../../../customers/types";
import i18n from "../../../i18n";
import { UserError } from "../../../types";

interface OrderAddressEditDialogProps {
  confirmButtonState: ConfirmButtonTransitionState;
  address: AddressTypeInput;
  open: boolean;
  errors: UserError[];
  variant: "billing" | "shipping" | string;
  countries?: Array<{
    code: string;
    label: string;
  }>;
  onClose();
  onConfirm(data: AddressTypeInput);
}

const OrderAddressEditDialog: React.StatelessComponent<
  OrderAddressEditDialogProps
> = ({
  address,
  confirmButtonState,
  open,
  errors,
  variant,
  countries,
  onClose,
  onConfirm
}) => (
  <Dialog open={open}>
    <Form initial={address} errors={errors} onSubmit={onConfirm}>
      {({ change, data, errors, submit }) => (
        <>
          <DialogTitle>
            {variant === "billing"
              ? i18n.t("Edit billing address", { context: "title" })
              : i18n.t("Edit shipping address", { context: "title" })}
          </DialogTitle>
          <DialogContent>
            <AddressEdit
              countries={countries}
              data={data}
              errors={errors}
              onChange={change}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>
              {i18n.t("Cancel", { context: "button" })}
            </Button>
            <ConfirmButton
              transitionState={confirmButtonState}
              color="primary"
              variant="raised"
              onClick={submit}
              type="submit"
            >
              {i18n.t("Confirm", { context: "button" })}
            </ConfirmButton>
          </DialogActions>
        </>
      )}
    </Form>
  </Dialog>
);
OrderAddressEditDialog.displayName = "OrderAddressEditDialog";
export default OrderAddressEditDialog;
