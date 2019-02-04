import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import Form from "../../../components/Form";
import Money from "../../../components/Money";
import { SingleSelectField } from "../../../components/SingleSelectField";
import i18n from "../../../i18n";
import { OrderDetails_order_availableShippingMethods } from "../../types/OrderDetails";

export interface FormData {
  shippingMethod: string;
}

const styles = (theme: Theme) =>
  createStyles({
    dialog: {
      overflowY: "visible"
    },
    menuItem: {
      display: "flex",
      width: "100%"
    },
    root: {
      overflowY: "visible",
      width: theme.breakpoints.values.sm
    },
    shippingMethodName: {
      flex: 1,
      overflowX: "hidden",
      textOverflow: "ellipsis"
    }
  });

interface OrderShippingMethodEditDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  open: boolean;
  shippingMethod: string;
  shippingMethods?: OrderDetails_order_availableShippingMethods[];
  onClose();
  onSubmit?(data: FormData);
}

const OrderShippingMethodEditDialog = withStyles(styles, {
  name: "OrderShippingMethodEditDialog"
})(
  ({
    classes,
    confirmButtonState,
    open,
    shippingMethod,
    shippingMethods,
    onClose,
    onSubmit
  }: OrderShippingMethodEditDialogProps) => {
    const choices = shippingMethods
      ? shippingMethods.map(s => ({
          label: (
            <div className={classes.menuItem}>
              <span className={classes.shippingMethodName}>{s.name}</span>
              &nbsp;
              <span>
                <Money money={s.price} />
              </span>
            </div>
          ),
          value: s.id
        }))
      : [];
    const initialForm: FormData = {
      shippingMethod
    };
    return (
      <Dialog open={open} classes={{ paper: classes.dialog }}>
        <DialogTitle>
          {i18n.t("Edit shipping method", { context: "title" })}
        </DialogTitle>
        <Form initial={initialForm} onSubmit={onSubmit}>
          {({ change, data }) => (
            <>
              <DialogContent className={classes.root}>
                <SingleSelectField
                  choices={choices}
                  name="shippingMethod"
                  value={data.shippingMethod}
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
  }
);
OrderShippingMethodEditDialog.displayName = "OrderShippingMethodEditDialog";
export default OrderShippingMethodEditDialog;
