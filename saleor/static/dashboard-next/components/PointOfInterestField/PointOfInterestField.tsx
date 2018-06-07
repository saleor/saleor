import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface PointOfInterestFieldProps {
  disabled?: boolean;
  src: string;
  value: string;
  onChange(event: any);
}

function hexToRgb(hex) {
  // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
  const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  hex = hex.replace(shorthandRegex, (m, r, g, b) => {
    return r + r + g + g + b + b;
  });

  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        b: parseInt(result[3], 16),
        g: parseInt(result[2], 16),
        r: parseInt(result[1], 16)
      }
    : null;
}

const decorate = withStyles(theme => {
  const color = hexToRgb(theme.palette.secondary.light);
  return {
    indicator: {
      backgroundColor: `rgba(${color.r}, ${color.g}, ${color.b}, .45)`,
      borderColor: theme.palette.secondary.main,
      borderRadius: "100%",
      borderStyle: "solid",
      borderWidth: 1,
      height: theme.spacing.unit * 4,
      position: "absolute" as "absolute",
      width: theme.spacing.unit * 4
    },
    root: {
      position: "relative" as "relative"
    }
  };
});
const PointOfInterestField = decorate<PointOfInterestFieldProps>(
  ({ classes, src, value, onChange, disabled }) => {
    return (
      <div className={classes.root}>
        <img src={src} />
        <div className={classes.indicator} />
      </div>
    );
  }
);
export default PointOfInterestField;
