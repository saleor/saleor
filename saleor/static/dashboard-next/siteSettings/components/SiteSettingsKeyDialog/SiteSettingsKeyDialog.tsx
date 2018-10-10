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
> = ({ errors, initial, open, onClose, onSubmit }) => (
  <Dialog maxWidth="xs" open={open}>
    <Form initial={initial} onSubmit={onSubmit} errors={errors}>
      {({ change, data }) => (
        <>
          <DialogTitle>
            {i18n.t("Add New Authorization Key", {
              context: "modal title"
            })}
          </DialogTitle>
          <DialogContent>
            <SingleSelectField
              choices={Object.keys(translatedAuthorizationKeyTypes()).map(
                key => ({
                  label: translatedAuthorizationKeyTypes()[key],
                  value: key
                })
              )}
              label={i18n.t("Authentication type", {
                context: "input label"
              })}
              name="type"
              onChange={change}
              value={data.type}
            />
            <FormSpacer />
            <TextField
              fullWidth
              label={i18n.t("Key", {
                context: "input label"
              })}
              name="key"
              onChange={change}
              value={data.key}
            />
            <FormSpacer />
            <TextField
              fullWidth
              label={i18n.t("Password", {
                context: "input label"
              })}
              name="password"
              onChange={change}
              value={data.password}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>
              {i18n.t("Cancel", { context: "button" })}
            </Button>
            <Button color="secondary" type="submit" variant="contained">
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
SiteSettingsKeyDialog.displayName = "SiteSettingsKeyDialog";
export default SiteSettingsKeyDialog;
