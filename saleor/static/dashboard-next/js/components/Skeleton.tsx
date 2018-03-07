import * as React from "react";
import { withStyles } from "material-ui";

const decorate = withStyles(theme => ({
  "@keyframes skeleton-animation": {
    "0%": {
      backgroundPosition: "-400px 0"
    },
    "100%": {
      backgroundPosition: "calc(200px + 100%) 0"
    }
  },
  skeleton: {
    animation: "skeleton-animation 1.4s ease-in-out infinite",
    backgroundImage:
      "linear-gradient(90deg, #eee, #eee 40%, #f5f5f5, #eee 60%, #eee)",
    borderRadius: 4,
    display: "block",
    height: "0.8em",
    margin: "0.2em 0"
  }
}));

interface SkeletonProps {
  style?: React.CSSProperties;
}

export const Skeleton = decorate<SkeletonProps>(({ classes, style }) => (
  <span className={classes.skeleton} style={style}>
    &zwnj;
  </span>
));
