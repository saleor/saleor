import { withStyles } from "material-ui/styles";
import * as React from "react";

interface ContainerProps {
  width: "xs" | "sm" | "md" | "lg" | "xl";
}

const decorate = withStyles(theme =>
  ["xs", "sm", "md", "lg", "xl"].reduce((prev, current) => {
    prev[current] = {
      [theme.breakpoints.up(current as any)]: {
        marginLeft: "auto",
        marginRight: "auto",
        maxWidth: theme.breakpoints.width(current as any)
      }
    };
    return prev;
  }, {})
);
export const Container = decorate<ContainerProps>(
  ({ classes, width, theme, ...props }) => (
    <div className={classes[width]} {...props} />
  )
);
export default Container;
