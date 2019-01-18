import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import classNames from "classnames";
import * as React from "react";

export type GridVariant = "default" | "inverted" | "uniform";
export interface GridProps extends WithStyles<typeof styles> {
  children: React.ReactNodeArray | React.ReactNode;
  variant?: GridVariant;
}

const styles = (theme: Theme) =>
  createStyles({
    default: {
      gridTemplateColumns: "9fr 4fr"
    },
    inverted: {
      gridTemplateColumns: "4fr 9fr"
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      [theme.breakpoints.down("sm")]: {
        "& > div": {
          marginBottom: theme.spacing.unit
        },
        gridTemplateColumns: "1fr"
      }
    },
    uniform: {
      gridTemplateColumns: "1fr 1fr"
    }
  });

export const Grid = withStyles(styles, { name: "Grid" })(
  ({ children, classes, variant }: GridProps) => (
    <div
      className={classNames({
        [classes.root]: true,
        [classes.default]: variant === "default",
        [classes.inverted]: variant === "inverted",
        [classes.uniform]: variant === "uniform"
      })}
    >
      {children}
    </div>
  )
);
Grid.displayName = "Grid";
Grid.defaultProps = {
  variant: "default"
};
export default Grid;
