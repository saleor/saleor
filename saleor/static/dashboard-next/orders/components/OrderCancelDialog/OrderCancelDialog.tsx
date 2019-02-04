import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogContentText from "@material-ui/core/DialogContentText";
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
} from "../../../components/ConfirmButton/ConfirmButton";
import ControlledCheckbox from "../../../components/ControlledCheckbox";
import Form from "../../../components/Form";
import i18n from "../../../i18n";

export interface FormData {
  restock: boolean;
}

const styles = (theme: Theme) =>
  createStyles({
    deleteButton: {
      "&:hover": {
        backgroundColor: theme.palette.error.main
      },
      backgroundColor: theme.palette.error.main,
      color: theme.palette.error.contrastText
    }
  });

interface OrderCancelDialogProps extends WithStyles<typeof styles> {
  confirmButtonState: ConfirmButtonTransitionState;
  number: string;
  open: boolean;
  onClose?();
  onSubmit(data: FormData);
}

const OrderCancelDialog = withStyles(styles, { name: "OrderCancelDialog" })(
  ({
    classes,
    confirmButtonState,
    number: orderNumber,
    open,
    onSubmit,
    onClose
  }: OrderCancelDialogProps) => (
    <Dialog open={open}>
      <Form
        initial={{
          restock: true
        }}
        onSubmit={onSubmit}
      >
        {({ data, change }) => {
          return (
            <>
              <DialogTitle>
                {i18n.t("Cancel order", { context: "title" })}
              </DialogTitle>
              <DialogContent>
                <DialogContentText
                  dangerouslySetInnerHTML={{
                    __html: i18n.t(
                      "Are you sure you want to cancel order <strong>{{ orderNumber }}</strong>?",
                      { orderNumber }
                    )
                  }}
                />
                <ControlledCheckbox
                  checked={data.restock}
                  label={i18n.t("Release all stock allocated to this order")}
                  name="restock"
                  onChange={change}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Back", { context: "button" })}
                </Button>
                <ConfirmButton
                  transitionState={confirmButtonState}
                  className={classes.deleteButton}
                  variant="contained"
                  type="submit"
                >
                  {i18n.t("Cancel order", { context: "button" })}
                </ConfirmButton>
              </DialogActions>
            </>
          );
        }}
      </Form>
    </Dialog>
  )
);
OrderCancelDialog.displayName = "OrderCancelDialog";
export default OrderCancelDialog;
