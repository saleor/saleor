import yellow from "@material-ui/core/colors/yellow";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";

const styles = (theme: Theme) => {
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
  return createStyles({
    errorDot: {
      "&:before": { backgroundColor: theme.palette.error.main, ...dot }
    },
    neutralDot: {
      "&:before": { backgroundColor: yellow[500], ...dot }
    },
    root: {
      display: "inline-block",
      marginLeft: theme.spacing.unit + 8,
      position: "relative"
    },
    span: {
      display: "inline"
    },
    successDot: {
      "&:before": { backgroundColor: theme.palette.primary.main, ...dot }
    }
  });
};

interface StatusLabelProps extends WithStyles<typeof styles> {
  className?: string;
  label: string | React.ReactNode;
  status: "success" | "neutral" | "error" | string;
  typographyProps?: TypographyProps;
}

const StatusLabel = withStyles(styles, { name: "StatusLabel" })(
  ({
    classes,
    className,
    label,
    status,
    typographyProps
  }: StatusLabelProps) => (
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
StatusLabel.displayName = "StatusLabel";
export default StatusLabel;
