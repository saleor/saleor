import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

const styles = createStyles({
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
    background: "#eee",
    borderRadius: 4,
    display: "block",
    height: "0.8em",
    margin: "0.2em 0"
  }
});

interface SkeletonProps extends WithStyles<typeof styles> {
  style?: React.CSSProperties;
}

const Skeleton = withStyles(styles, { name: "Skeleton" })(
  ({ classes, style }: SkeletonProps) => (
    <span className={classes.skeleton} style={style}>
      &zwnj;
    </span>
  )
);

Skeleton.displayName = "Skeleton";
export default Skeleton;
