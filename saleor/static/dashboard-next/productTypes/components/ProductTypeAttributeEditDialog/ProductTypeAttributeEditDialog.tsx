import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import Form from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import ListField from "../../../components/ListField/ListField";
import i18n from "../../../i18n";

export interface FormData {
  name: string;
  values: string[];
}

interface ProductTypeAttributeEditDialogProps {
  name: string;
  opened: boolean;
  title: string;
  values: string[];
  onClose: () => void;
  onConfirm: (data: FormData) => void;
}

const decorate = withStyles({ root: {} });
const ProductTypeAttributeEditDialog = decorate<
  ProductTypeAttributeEditDialogProps
>(({ name, opened, title, values, onClose, onConfirm }) => {
  const initialForm: FormData = {
    name: name || "",
    values: values || []
  };
  return (
    <Dialog open={opened}>
      <Form initial={initialForm} onSubmit={onConfirm}>
        {({ change, data }) => (
          <>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
              <TextField
                fullWidth
                label={i18n.t("Attribute name")}
                name="name"
                value={data.name}
                onChange={change}
              />
              <FormSpacer />
              <ListField
                autoComplete="off"
                fullWidth
                name="values"
                label={i18n.t("Attribute values")}
                values={data.values}
                onChange={change}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={onClose}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
              <Button color="primary" variant="raised" type="submit">
                {i18n.t("Save", { context: "button" })}
              </Button>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  );
});
ProductTypeAttributeEditDialog.displayName = "ProductTypeAttributeEditDialog";
export default ProductTypeAttributeEditDialog;
