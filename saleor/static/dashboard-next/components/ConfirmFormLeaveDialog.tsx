import * as React from "react";
import NavigationPrompt from "react-router-navigation-prompt";

import DialogContentText from "@material-ui/core/DialogContentText";
import i18n from "../i18n";
import ActionDialog from "./ActionDialog";
import { FormContext } from "./Form";

export const ConfirmFormLeaveDialog: React.StatelessComponent<{}> = () => (
  <FormContext.Consumer>
    {({ hasChanged: hasFormChanged }) => (
      <NavigationPrompt renderIfNotActive={true} when={hasFormChanged}>
        {({ isActive, onCancel, onConfirm }) => (
          <ActionDialog
            open={isActive}
            onClose={onCancel}
            onConfirm={onConfirm}
            confirmButtonState="default"
            title={i18n.t("Leaving form", {
              context: "modal title"
            })}
          >
            <DialogContentText>
              {i18n.t("Are you sure you want to leave unsaved changes?", {
                context: "form leave confirmation"
              })}
            </DialogContentText>
          </ActionDialog>
        )}
      </NavigationPrompt>
    )}
  </FormContext.Consumer>
);
