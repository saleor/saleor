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
    content: "''",
    display: "block",
    height: 8,
    left: -theme.spacing.unit * 2,
    position: "absolute" as "absolute",
    top: "calc(50% - 5px)",
    width: 8
  };
  return {
    errorDot: {
      "&:before": { backgroundColor: theme.palette.error.main, ...dot }
    },
    neutralDot: {
      "&:before": { backgroundColor: yellow[500], ...dot }
    },
    root: {
      display: "inline-block",
      marginLeft: theme.spacing.unit + 8,
      position: "relative" as "relative"
    },
    span: {
      display: "inline"
    },
    successDot: {
      "&:before": { backgroundColor: theme.palette.primary.main, ...dot }
    }
  };
});
const StatusLabel = decorate<StatusLabelProps>(
  ({ classes, className, label, status, typographyProps }) => (
    <div
      className={classNames({
        [classes.root]: true,
        [className]: true,
        [classes.successDot]: status === "success",
        [classes.neutralDot]: status === "neutral",
        [classes.errorDot]: status === "error"
      })}
    >
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
