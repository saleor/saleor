import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

const decorate = withStyles(
  {
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
  },
  { name: "Skeleton" }
);

interface SkeletonProps {
  style?: React.CSSProperties;
}

const Skeleton = decorate<SkeletonProps>(({ classes, style }) => (
  <span className={classes.skeleton} style={style}>
    &zwnj;
  </span>
));

export default Skeleton;
