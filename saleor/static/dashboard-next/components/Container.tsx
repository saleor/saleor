import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      [theme.breakpoints.up("lg")]: {
        marginLeft: "auto",
        marginRight: "auto",
        maxWidth: theme.breakpoints.width("lg")
      }
    }
  });

interface ContainerProps extends WithStyles<typeof styles> {
  className?: string;
}

export const Container = withStyles(styles, {
  name: "Container"
})(({ classes, className, ...props }: ContainerProps) => (
  <div className={classNames(classes.root, className)} {...props} />
));
Container.displayName = "Container";
export default Container;
