import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { CSSProperties } from "@material-ui/core/styles/withStyles";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles(
    ["xs", "sm", "md", "lg", "xl"].reduce<Record<string, CSSProperties>>(
      (prev, current) => {
        prev[current] = {
          [theme.breakpoints.up(current as any)]: {
            marginLeft: "auto",
            marginRight: "auto",
            maxWidth: theme.breakpoints.width(current as any)
          }
        };
        return prev;
      },
      {}
    )
  );

interface ContainerProps extends WithStyles<typeof styles, true> {
  className?: string;
  width: "xs" | "sm" | "md" | "lg" | "xl";
}

export const Container = withStyles(styles, {
  name: "Container",
  withTheme: true
})(({ classes, className, width, theme, ...props }: ContainerProps) => (
  <div className={classNames(classes[width], className)} {...props} />
));
Container.displayName = "Container";
export default Container;
