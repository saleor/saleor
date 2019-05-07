import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import ConfirmButton, {
  ConfirmButtonTransitionState
} from "../../../components/ConfirmButton";
import i18n from "../../../i18n";

interface TranslationFieldsSaveProps {
  saveButtonState: ConfirmButtonTransitionState;
  onDiscard: () => void;
  onSave: () => void;
}

const styles = (theme: Theme) =>
  createStyles({
    confirmButton: {
      marginLeft: theme.spacing.unit
    },
    root: {
      display: "flex",
      flexDirection: "row-reverse",
      marginTop: theme.spacing.unit
    }
  });

const TranslationFieldsSave = withStyles(styles, {
  name: "TranslationFieldsSave"
})(
  ({
    classes,
    saveButtonState,
    onDiscard,
    onSave
  }: TranslationFieldsSaveProps & WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <ConfirmButton
        className={classes.confirmButton}
        transitionState={saveButtonState}
        onClick={onSave}
      >
        {i18n.t("Save")}
      </ConfirmButton>
      <Button onClick={onDiscard}>{i18n.t("Discard Changes")}</Button>
    </div>
  )
);
TranslationFieldsSave.displayName = "TranslationFieldsSave";
export default TranslationFieldsSave;
