import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import gray from "@material-ui/core/colors/grey";
import { withStyles } from "@material-ui/core/styles";
import CheckIcon from "@material-ui/icons/Check";
import * as React from "react";
import i18n from "../../i18n";

export type SaveButtonBarState =
  | "loading"
  | "success"
  | "error"
  | "default"
  | string;
interface SaveButtonBarProps {
  disabled?: boolean;
  state?: SaveButtonBarState;
  labels?: {
    cancel?: string;
    delete?: string;
    save?: string;
  };
  onCancel: () => void;
  onDelete?: () => void;
  onSave(event: any);
}

const decorate = withStyles(theme => ({
  button: {
    marginRight: theme.spacing.unit
  },
  buttonProgress: {
    "& svg": {
      margin: 0
    },
    color: theme.palette.primary.main,
    marginBottom: -theme.spacing.unit * 1.5,
    marginLeft: -theme.spacing.unit * 0.5,
    marginRight: theme.spacing.unit * 0.5,
    marginTop: -theme.spacing.unit * 1.5,
    position: "relative" as "relative"
  },
  cancelButton: {
    marginRight: theme.spacing.unit * 2
  },
  deleteButton: {
    "&:hover": {
      backgroundColor: theme.palette.error.dark
    },
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText
  },
  error: {
    "&:hover": {
      backgroundColor: theme.palette.error.main
    },
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText
  },
  icon: {
    marginBottom: -theme.spacing.unit * 1.5,
    marginRight: theme.spacing.unit * 0.5,
    marginTop: -theme.spacing.unit * 1.5,
    position: "relative" as "relative"
  },
  root: {
    borderTop: `1px ${gray[300]} solid`,
    display: "flex",
    marginBottom: theme.spacing.unit * 2,
    marginTop: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  spacer: {
    flex: "1"
  },
  success: {
    "&:hover": {
      backgroundColor: theme.palette.primary.main
    },
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText
  }
}));
export const SaveButtonBar = decorate<SaveButtonBarProps>(
  ({
    classes,
    disabled,
    labels,
    state,
    onCancel,
    onDelete,
    onSave,
    ...props
  }) => {
    let buttonClassName;
    let buttonLabel;
    switch (state) {
      case "success":
        buttonClassName = classes.success;
        buttonLabel = i18n.t("Saved");
        break;
      case "error":
        buttonClassName = classes.error;
        buttonLabel = i18n.t("Error");
        break;
      case "loading":
        buttonClassName = "";
        buttonLabel = i18n.t("Saving");
        break;
      default:
        buttonClassName = "";
        buttonLabel = labels && labels.save ? labels.save : i18n.t("Save");
        break;
    }
    return (
      <div className={classes.root} {...props}>
        {!!onDelete && (
          <Button
            variant="contained"
            onClick={onDelete}
            className={classes.deleteButton}
          >
            {labels && labels.delete ? labels.delete : i18n.t("Remove")}
          </Button>
        )}
        <div className={classes.spacer} />
        <Button
          className={classes.cancelButton}
          variant="flat"
          onClick={onCancel}
        >
          {labels && labels.cancel ? labels.cancel : i18n.t("Cancel")}
        </Button>
        <Button
          variant="contained"
          onClick={onSave}
          color="secondary"
          disabled={disabled || state === "loading"}
          className={buttonClassName}
        >
          {state === "loading" && (
            <CircularProgress
              size={24}
              color="secondary"
              className={classes.buttonProgress}
            />
          )}
          {state === "success" && <CheckIcon className={classes.icon} />}
          {buttonLabel}
        </Button>
      </div>
    );
  }
);
SaveButtonBar.displayName = "SaveButtonBar";
export default SaveButtonBar;
