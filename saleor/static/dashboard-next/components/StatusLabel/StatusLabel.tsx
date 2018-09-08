import yellow from "@material-ui/core/colors/yellow";
import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

interface StatusLabelProps {
  className?: string;
  label: string;
  status: "success" | "neutral" | "error" | string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => {
  const dot = {
    borderRadius: "100%",
    display: "inline-block",
    height: theme.spacing.unit,
    marginBottom: 1,
    marginRight: theme.spacing.unit,
    width: theme.spacing.unit
  };
  return {
    errorDot: {
      ...dot,
      backgroundColor: theme.palette.error.main
    },
    neutralDot: {
      ...dot,
      backgroundColor: yellow[500]
    },
    root: {
      display: "inline-block"
    },
    span: {
      display: "inline"
    },
    successDot: {
      ...dot,
      backgroundColor: theme.palette.primary.main
    }
  };
});
const StatusLabel = decorate<StatusLabelProps>(
  ({ classes, className, label, status, typographyProps }) => (
    <div className={classNames(classes.root, className)}>
      <span
        className={
          status === "success"
            ? classes.successDot
            : status === "neutral"
              ? classes.neutralDot
              : classes.errorDot
        }
      />
      {typographyProps ? (
        <Typography
          component="span"
          className={classes.span}
          {...typographyProps}
        >
          {label}
        </Typography>
      ) : (
        label
      )}
    </div>
  )
);
export default StatusLabel;
