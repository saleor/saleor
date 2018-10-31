import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

interface ContainerProps {
  className?: string;
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
  ({ classes, className, width, theme, ...props }) => (
    <div className={classNames(classes[width], className)} {...props} />
  )
);
Container.displayName = "Container";
export default Container;
