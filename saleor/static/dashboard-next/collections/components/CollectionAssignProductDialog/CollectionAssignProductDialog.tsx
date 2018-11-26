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
  product: {
    label: string;
    value: string;
  };
}

interface CollectionAssignProductDialogProps {
  open: boolean;
  products: Array<{
    id: string;
    name: string;
  }>;
  loading: boolean;
  fetch: (value: string) => void;
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
  product: {
    label: "",
    value: ""
  }
};
const CollectionAssignProductDialog = decorate<
  CollectionAssignProductDialogProps
>(({ classes, open, loading, products, fetch, onClose, onSubmit }) => (
  <Dialog
    open={open}
    classes={{ paper: classes.overflow }}
    fullWidth
    maxWidth="sm"
  >
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ data, change }) => {
        const choices =
          !loading && products
            ? products.map(product => ({
                label: product.name,
                value: product.id
              }))
            : [];
        return (
          <>
            <DialogTitle>{i18n.t("Add product")}</DialogTitle>
            <DialogContent className={classes.overflow}>
              <SingleAutocompleteSelectField
                name="product"
                value={data.product}
                choices={choices}
                onChange={change}
                fetchChoices={fetch}
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
));
CollectionAssignProductDialog.displayName = "CollectionAssignProductDialog";
export default CollectionAssignProductDialog;
