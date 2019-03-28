import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../../i18n";

interface TranslationFieldsSaveProps {
  onDiscard: () => void;
  onSave: () => void;
}

const styles = (theme: Theme) =>
  createStyles({
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
    onDiscard,
    onSave
  }: TranslationFieldsSaveProps & WithStyles<typeof styles>) => (
    <div className={classes.root}>
      <Button color="primary" onClick={onSave}>
        {i18n.t("Save")}
      </Button>
      <Button onClick={onDiscard}>{i18n.t("Discard")}</Button>
    </div>
  )
);
TranslationFieldsSave.displayName = "TranslationFieldsSave";
export default TranslationFieldsSave;
