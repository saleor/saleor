import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import Form, { FormProps } from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import SingleSelectField from "../../../components/SingleSelectField";
import i18n from "../../../i18n";
import { translatedAuthorizationKeyTypes } from "../../../misc";
import { AuthorizationKeyType } from "../../../types/globalTypes";

export interface SiteSettingsKeyDialogForm {
  key: string;
  password: string;
  type: AuthorizationKeyType;
}

export interface SiteSettingsKeyDialogProps
  extends Pick<
      FormProps<SiteSettingsKeyDialogForm>,
      Exclude<keyof FormProps<SiteSettingsKeyDialogForm>, "children">
    > {
  open: boolean;
  onClose: () => void;
}

const SiteSettingsKeyDialog: React.StatelessComponent<
  SiteSettingsKeyDialogProps
> = ({ errors, initial, open, onClose, onSubmit }) => {
  const keyTypes = translatedAuthorizationKeyTypes();
  return (
    <Dialog maxWidth="xs" open={open}>
      <Form initial={initial} onSubmit={onSubmit} errors={errors}>
        {({ change, data, errors }) => (
          <>
            <DialogTitle>
              {i18n.t("Add New Authorization Key", {
                context: "modal title"
              })}
            </DialogTitle>
            <DialogContent>
              <SingleSelectField
                choices={Object.keys(keyTypes).map(key => ({
                  label: keyTypes[key],
                  value: key
                }))}
                error={!!errors.keyType}
                label={i18n.t("Authentication type", {
                  context: "input label"
                })}
                hint={errors.keyType}
                name="type"
                onChange={change}
                value={data.type}
              />
              <FormSpacer />
              <TextField
                error={!!errors.key}
                fullWidth
                label={i18n.t("Key", {
                  context: "input label"
                })}
                helperText={errors.key}
                name="key"
                onChange={change}
                value={data.key}
              />
              <FormSpacer />
              <TextField
                error={!!errors.password}
                fullWidth
                label={i18n.t("Password", {
                  context: "input label"
                })}
                helperText={errors.password}
                name="password"
                onChange={change}
                value={data.password}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={onClose}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
              <Button color="primary" type="submit" variant="contained">
                {i18n.t("Add authentication", {
                  context: "button"
                })}
              </Button>
            </DialogActions>
          </>
        )}
      </Form>
    </Dialog>
  );
};
SiteSettingsKeyDialog.displayName = "SiteSettingsKeyDialog";
export default SiteSettingsKeyDialog;
