import yellow from "@material-ui/core/colors/yellow";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

interface StatusLabelProps {
  label: string;
  status: string;
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
    span: {
      display: "inline"
    },
    successDot: {
      ...dot,
      backgroundColor: theme.palette.primary.main
    }
  };
});
const StatusLabel = decorate<StatusLabelProps>(({ classes, label, status }) => (
  <>
    <span
      className={
        status === "success"
          ? classes.successDot
          : status === "neutral"
            ? classes.neutralDot
            : classes.errorDot
      }
    />
    <Typography component="span" className={classes.span}>
      {label}
    </Typography>
  </>
));
export default StatusLabel;
