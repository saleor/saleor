import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit";
import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { AddressTypeInput } from "../../types";
import { CustomerAddresses_user_addresses } from "../../types/CustomerAddresses";

export interface CustomerAddressDialogProps {
  address: CustomerAddresses_user_addresses;
  confirmButtonState: ConfirmButtonTransitionState;
  countries: Array<{
    code: string;
    label: string;
  }>;
  errors: UserError[];
  open: boolean;
  variant: "create" | "edit";
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
    variant,
    onClose,
    onConfirm
  }: CustomerAddressDialogProps & WithStyles<typeof styles>) => {
    const initialForm: AddressTypeInput = {
      city: maybe(() => address.city, ""),
      cityArea: maybe(() => address.cityArea, ""),
      companyName: maybe(() => address.companyName, ""),
      country: {
        label: maybe(() => address.country.country, ""),
        value: maybe(() => address.country.code, "")
      },
      countryArea: maybe(() => address.countryArea, ""),
      firstName: maybe(() => address.firstName, ""),
      lastName: maybe(() => address.lastName, ""),
      phone: maybe(() => address.phone, ""),
      postalCode: maybe(() => address.postalCode, ""),
      streetAddress1: maybe(() => address.streetAddress1, ""),
      streetAddress2: maybe(() => address.streetAddress2, "")
    };
    return (
      <Dialog
        open={open}
        classes={{ paper: classes.overflow }}
        fullWidth
        maxWidth="sm"
      >
        <Form initial={initialForm} errors={errors} onSubmit={onConfirm}>
          {({ change, data, errors, submit }) => (
            <>
              <DialogTitle>
                {variant === "create"
                  ? i18n.t("Add Address")
                  : i18n.t("Edit Address")}
              </DialogTitle>
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
                  {i18n.t("Save Address", { context: "button" })}
                  <AddIcon />
                </ConfirmButton>
              </DialogActions>
            </>
          )}
        </Form>
      </Dialog>
    );
  }
);
CustomerAddressDialog.displayName = "CustomerAddressDialog";
export default CustomerAddressDialog;
