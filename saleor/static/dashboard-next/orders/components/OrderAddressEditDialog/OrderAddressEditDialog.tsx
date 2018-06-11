import Button from "@material-ui/core/Button";
import Dialog, { DialogProps } from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import PhoneField from "../../../components/PhoneField";
import SingleSelectField from "../../../components/SingleSelectField";
import { AddressType } from "../../../customers/";
import i18n from "../../../i18n";
import AddressEdit from "../../../components/AddressEdit/AddressEdit";

interface OrderAddressEditDialogProps {
  open: boolean;
  data: AddressType;
  variant: "billing" | "shipping" | string;
  countries?: Array<{
    code: string;
    label: string;
  }>;
  prefixes: string[];
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(
  theme => ({
    root: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  }),
  { name: "OrderAddressEditDialog" }
);
const OrderAddressEditDialog = decorate<OrderAddressEditDialogProps>(
  ({
    children,
    classes,
    open,
    variant,
    countries,
    data,
    prefixes,
    onConfirm,
    onClose,
    onChange
  }) => (
    <Dialog open={open}>
      <DialogTitle>
        {variant === "billing"
          ? i18n.t("Edit billing address", { context: "title" })
          : i18n.t("Edit shipping address", { context: "title" })}
      </DialogTitle>
      <DialogContent>
        <AddressEdit
          countries={countries}
          data={data}
          onChange={onChange}
          prefixes={prefixes}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {i18n.t("Confirm", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  )
);
export default OrderAddressEditDialog;
