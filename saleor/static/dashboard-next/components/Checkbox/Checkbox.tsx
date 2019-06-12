import { Omit } from "@material-ui/core";
import ButtonBase from "@material-ui/core/ButtonBase";
import { CheckboxProps as MuiCheckboxProps } from "@material-ui/core/Checkbox";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import classNames from "classnames";
import * as React from "react";

export type CheckboxProps = Omit<
  MuiCheckboxProps,
  | "checkedIcon"
  | "color"
  | "icon"
  | "indeterminateIcon"
  | "classes"
  | "onChange"
> & {
  onChange?: () => void;
};

const styles = (theme: Theme) =>
  createStyles({
    box: {
      "&$checked": {
        "&:before": {
          background: theme.palette.primary.main
        },
        borderColor: theme.palette.primary.main
      },
      "&$disabled": {
        borderColor: theme.palette.grey[200]
      },
      "&$indeterminate": {
        "&:before": {
          background: theme.palette.primary.main,
          height: 2,
          top: 5
        },
        borderColor: theme.palette.primary.main
      },
      "&:before": {
        background: "rgba(0, 0, 0, 0)",
        borderRadius: 2,
        content: '""',
        height: 8,
        left: 2,
        position: "absolute",
        top: 2,
        transition: theme.transitions.duration.short + "ms",
        width: 8
      },
      WebkitAppearance: "none",
      border: `1px solid ${theme.palette.grey[500]}`,
      borderRadius: 4,
      boxSizing: "border-box",
      cursor: "pointer",
      height: 14,
      outline: "0",
      position: "relative",
      userSelect: "none",
      width: 14
    },
    checked: {},
    disabled: {},
    indeterminate: {},
    root: {
      alignItems: "center",
      borderRadius: "100%",
      cursor: "pointer",
      display: "flex",
      height: 48,
      justifyContent: "center",
      width: 48
    }
  });
const Checkbox = withStyles(styles, { name: "Checkbox" })(
  ({
    checked,
    className,
    classes,
    disabled,
    indeterminate,
    onChange,
    onClick,
    value,
    name,
    ...props
  }: CheckboxProps & WithStyles<typeof styles>) => {
    const inputRef = React.useRef<HTMLInputElement>(null);
    return (
      <ButtonBase
        {...props}
        centerRipple
        className={classNames(classes.root, className)}
        disabled={disabled}
        onClick={onClick}
      >
        <input
          className={classNames(classes.box, {
            [classes.checked]: checked,
            [classes.disabled]: disabled,
            [classes.indeterminate]: indeterminate
          })}
          disabled={disabled}
          type="checkbox"
          name={name}
          value={checked !== undefined && checked.toString()}
          ref={inputRef}
          onChange={onChange}
        />
      </ButtonBase>
    );
  }
);
Checkbox.displayName = "Checkbox";
export default Checkbox;
