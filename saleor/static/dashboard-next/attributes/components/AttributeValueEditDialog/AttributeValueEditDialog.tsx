import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "@saleor/components/ConfirmButton";
import Form from "@saleor/components/Form";
import FormSpacer from "@saleor/components/FormSpacer";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { UserError } from "@saleor/types";
import { AttributeDetails_attribute_values } from "../../types/AttributeDetails";

export interface AttributeValueEditDialogFormData {
  name: string;
  slug: string;
}
export interface AttributeValueEditDialogProps {
  attributeValue: AttributeDetails_attribute_values | null;
  confirmButtonState: ConfirmButtonTransitionState;
  disabled: boolean;
  errors: UserError[];
  open: boolean;
  onSubmit: (data: AttributeValueEditDialogFormData) => void;
  onClose: () => void;
}

const AttributeValueEditDialog: React.StatelessComponent<
  AttributeValueEditDialogProps
> = ({
  attributeValue,
  confirmButtonState,
  disabled,
  errors,
  onClose,
  onSubmit,
  open
}) => {
  const initialForm = {
    name: maybe(() => attributeValue.name, ""),
    slug: maybe(() => attributeValue.slug, "")
  };

  return (
    <Dialog onClose={onClose} open={open} fullWidth maxWidth="sm">
      <DialogTitle>
        {attributeValue === null
          ? i18n.t("Add Value", {
              context: "add attribute value"
            })
          : i18n.t("Edit Value", {
              context: "edit attribute value"
            })}
      </DialogTitle>
      <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
        {({ change, data, errors: formErrors, submit }) => (
          <>
            <DialogContent>
              <TextField
                disabled={disabled}
                error={!!formErrors.slug}
                fullWidth
                helperText={formErrors.slug}
                name={"slug" as keyof AttributeValueEditDialogFormData}
                label={i18n.t("Admin name", {
                  context: "attribute slug"
                })}
                value={data.slug}
                onChange={change}
              />
              <FormSpacer />
              <TextField
                disabled={disabled}
                error={!!formErrors.name}
                fullWidth
                helperText={formErrors.name}
                name={"name" as keyof AttributeValueEditDialogFormData}
                label={i18n.t("Default Storefront Name", {
                  context: "attribute name"
                })}
                value={data.name}
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
              >
                {i18n.t("Save")}
              </ConfirmButton>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  );
};
AttributeValueEditDialog.displayName = "AttributeValueEditDialog";
export default AttributeValueEditDialog;
