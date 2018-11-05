import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Form from "../../../components/Form";
import Money from "../../../components/Money";
import { SingleSelectField } from "../../../components/SingleSelectField";
import i18n from "../../../i18n";
import { OrderDetails_order_availableShippingMethods } from "../../types/OrderDetails";

export interface FormData {
  shippingMethod: string;
}

interface OrderShippingMethodEditDialogProps {
  open: boolean;
  shippingMethod: string;
  shippingMethods?: OrderDetails_order_availableShippingMethods[];
  onClose();
  onSubmit?(data: FormData);
}

const decorate = withStyles(
  theme => ({
    dialog: {
      overflowY: "visible" as "visible"
    },
    menuItem: {
      display: "flex" as "flex",
      width: "100%"
    },
    root: {
      overflowY: "visible" as "visible",
      width: theme.breakpoints.values.sm
    },
    shippingMethodName: {
      flex: 1,
      overflowX: "hidden" as "hidden",
      textOverflow: "ellipsis" as "ellipsis"
    }
  }),
  { name: "OrderShippingMethodEditDialog" }
);
const OrderShippingMethodEditDialog = decorate<
  OrderShippingMethodEditDialogProps
>(({ classes, open, shippingMethod, shippingMethods, onClose, onSubmit }) => {
  const choices = shippingMethods
    ? shippingMethods.map(s => ({
        label: (
          <div className={classes.menuItem}>
            <span className={classes.shippingMethodName}>{s.name}</span>
            &nbsp;
            <span>
              <Money moneyDetalis={s.price} />
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
              <Button color="primary" variant="raised" type="submit">
                {i18n.t("Confirm", { context: "button" })}
              </Button>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  );
});
export default OrderShippingMethodEditDialog;
