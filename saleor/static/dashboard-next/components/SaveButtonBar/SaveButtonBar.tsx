import Button from "@material-ui/core/Button";
import gray from "@material-ui/core/colors/grey";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import i18n from "../../i18n";

interface SaveButtonBarProps {
  disabled?: boolean;
  onBack(event: any);
  onSave(event: any);
}

const decorate = withStyles(theme => ({
  root: {
    borderTop: `1px ${gray[300]} solid`,
    display: "flex",
    marginTop: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  spacer: {
    flex: "1"
  },
  button: {
    marginRight: theme.spacing.unit
  }
}));
export const SaveButtonBar = decorate<SaveButtonBarProps>(
  ({ classes, disabled, onBack, onSave, ...props }) => (
    <div className={classes.root}>
      <div className={classes.spacer} />
      <Button onClick={onBack} className={classes.button}>
        {i18n.t("Cancel")}
      </Button>
      <Button
        variant="raised"
        onClick={onSave}
        color="primary"
        disabled={disabled}
      >
        {i18n.t("Save")}
      </Button>
    </div>
  )
);
export default SaveButtonBar;
