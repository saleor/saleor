import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    "@keyframes skeleton-animation": {
      "0%": {
        opacity: 0.6
      },
      "100%": {
        opacity: 1
      }
    },
    skeleton: {
      animation: "skeleton-animation .75s linear infinite forwards alternate",
      background: theme.palette.background.default,
      borderRadius: 4,
      display: "block",
      height: "0.8em",
      margin: "0.2em 0"
    }
  });

interface SkeletonProps extends WithStyles<typeof styles> {
  className?: string;
  style?: React.CSSProperties;
}

const Skeleton = withStyles(styles, { name: "Skeleton" })(
  ({ className, classes, style }: SkeletonProps) => (
    <span className={classNames(classes.skeleton, className)} style={style}>
      &zwnj;
    </span>
  )
);

Skeleton.displayName = "Skeleton";
export default Skeleton;
