import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import gray from "@material-ui/core/colors/grey";
import { withStyles } from "@material-ui/core/styles";
import CheckIcon from "@material-ui/icons/Check";
import classNames from "classnames";
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
      color: theme.palette.common.white,
      margin: 0
    },
    opacity: 0,
    position: "absolute" as "absolute",
    transition: theme.transitions.duration.standard + "ms"
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
    marginLeft: "0 !important",
    opacity: 0,
    position: "absolute" as "absolute",
    transition: theme.transitions.duration.standard + "ms"
  },
  label: {
    transition: theme.transitions.duration.standard + "ms"
  },
  labelInvisible: {
    opacity: 0
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
  },
  visible: {
    opacity: 1
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
    let saveButtonClassName;
    let buttonLabel;
    switch (state) {
      case "success":
        saveButtonClassName = classes.success;
        buttonLabel = i18n.t("Save");
        break;
      case "error":
        saveButtonClassName = classes.error;
        buttonLabel = i18n.t("Error");
        break;
      case "loading":
        saveButtonClassName = "";
        buttonLabel = i18n.t("Save");
        break;
      default:
        saveButtonClassName = "";
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
          onClick={state === "loading" ? undefined : onSave}
          color="secondary"
          disabled={disabled}
          className={saveButtonClassName}
        >
          <CircularProgress
            size={24}
            color="inherit"
            className={classNames({
              [classes.buttonProgress]: true,
              [classes.visible]: state === "loading"
            })}
          />
          <CheckIcon
            className={classNames({
              [classes.icon]: true,
              [classes.visible]: state === "success"
            })}
          />
          <span
            className={classNames({
              [classes.label]: true,
              [classes.labelInvisible]:
                state === "loading" || state === "success"
            })}
          >
            {buttonLabel}
          </span>
        </Button>
      </div>
    );
  }
);
SaveButtonBar.displayName = "SaveButtonBar";
export default SaveButtonBar;
