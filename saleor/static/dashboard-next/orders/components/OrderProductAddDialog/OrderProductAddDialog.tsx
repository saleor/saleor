import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Form from "../../../components/Form";
import { SingleAutocompleteSelectField } from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

export interface FormData {
  quantity: number;
  variant: {
    label: string;
    value: string;
  };
}

interface OrderProductAddDialogProps {
  open: boolean;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    stockQuantity: number;
  }>;
  loading: boolean;
  fetchVariants: (value: string) => void;
  onClose: () => void;
  onSubmit: (data: FormData) => void;
}

const decorate = withStyles(
  {
    overflow: {
      overflowY: "visible" as "visible"
    }
  },
  { name: "OrderProductAddDialog" }
);
const initialForm: FormData = {
  quantity: 1,
  variant: {
    label: "",
    value: ""
  }
};
const OrderProductAddDialog = decorate<OrderProductAddDialogProps>(
  ({ classes, open, loading, variants, fetchVariants, onClose, onSubmit }) => (
    <Dialog
      open={open}
      classes={{ paper: classes.overflow }}
      fullWidth
      maxWidth="sm"
    >
      <Form initial={initialForm} onSubmit={onSubmit}>
        {({ data, change }) => {
          const choices =
            !loading && variants
              ? variants.map(v => ({
                  label: `${v.sku} ${v.name}`,
                  value: v.id
                }))
              : [];
          return (
            <>
              <DialogTitle>{i18n.t("Add product")}</DialogTitle>
              <DialogContent className={classes.overflow}>
                <SingleAutocompleteSelectField
                  name="variant"
                  value={data.variant}
                  choices={choices}
                  onChange={change}
                  fetchChoices={fetchVariants}
                  loading={loading}
                />
              </DialogContent>
              <DialogActions>
                <Button onClick={onClose}>
                  {i18n.t("Cancel", { context: "button" })}
                </Button>
                <Button color="primary" variant="contained" type="submit">
                  {i18n.t("Confirm", { context: "button" })}
                </Button>
              </DialogActions>
            </>
          );
        }}
      </Form>
    </Dialog>
  )
);
OrderProductAddDialog.displayName = "OrderProductAddDialog";
export default OrderProductAddDialog;
