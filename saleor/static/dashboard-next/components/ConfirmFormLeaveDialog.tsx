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
import NavigationPrompt from "react-router-navigation-prompt";

import i18n from "../i18n";
import { FormContext } from "./Form";

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

export const ConfirmFormLeaveDialog = withStyles(styles, {
  name: "ConfirmFormLeaveDialog"
})(({ classes }: WithStyles<typeof styles>) => (
  <FormContext.Consumer>
    {({ hasChanged: hasFormChanged }) => (
      <NavigationPrompt renderIfNotActive={true} when={hasFormChanged}>
        {({ isActive, onCancel, onConfirm }) => (
          <Dialog open={isActive}>
            <DialogTitle>{i18n.t("Unsaved changes")}</DialogTitle>
            <DialogContent>
              <DialogContentText>
                {i18n.t(
                  "If you leave this page, unsaved changes will be lost. Are you sure you want to leave?",
                  {
                    context: "form leave confirmation"
                  }
                )}
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={onCancel}>
                {i18n.t("Cancel", { context: "button" })}
              </Button>
              <Button onClick={onConfirm} className={classes.deleteButton}>
                {i18n.t("Leave page", { context: "button" })}
              </Button>
            </DialogActions>
          </Dialog>
        )}
      </NavigationPrompt>
    )}
  </FormContext.Consumer>
));
