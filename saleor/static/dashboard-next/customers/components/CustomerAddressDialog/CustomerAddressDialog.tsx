import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import { AddressTypeInput } from "../../types";
import { CustomerAddresses_user } from "../../types/CustomerAddresses";

export interface CustomerAddressDialogProps {
  address: AddressTypeInput;
  confirmButtonState: ConfirmButtonTransitionState;
  countries: Array<{
    code: string;
    label: string;
  }>;
  errors: UserError[];
  open: boolean;
  user: CustomerAddresses_user;
  onClose: () => void;
  onConfirm: (data: AddressTypeInput) => void;
}

const styles = createStyles({
  overflow: {
    overflowY: "visible"
  }
});

const CustomerAddressDialog = withStyles(styles, {})(
  ({
    address,
    classes,
    confirmButtonState,
    countries,
    errors,
    open,
    user,
    onClose,
    onConfirm
  }: CustomerAddressDialogProps & WithStyles<typeof styles>) => (
    <Dialog open={open} classes={{ paper: classes.overflow }}>
      <Form initial={address} errors={errors} onSubmit={onConfirm}>
        {({ change, data, errors, submit }) => (
          <>
            <DialogTitle>{}</DialogTitle>
            <DialogContent className={classes.overflow}>
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
                variant="contained"
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
  )
);
CustomerAddressDialog.displayName = "CustomerAddressDialog";
export default CustomerAddressDialog;
