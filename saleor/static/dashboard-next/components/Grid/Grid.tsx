import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

interface GridProps extends WithStyles<typeof styles> {
  children: React.ReactNodeArray | React.ReactNode;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "9fr 4fr",
      [theme.breakpoints.down("sm")]: {
        "& > div": {
          marginBottom: theme.spacing.unit
        },
        gridTemplateColumns: "1fr"
      }
    }
  });

export const Grid = withStyles(styles, { name: "Grid" })(
  ({ children, classes }: GridProps) => (
    <div className={classes.root}>{children}</div>
  )
);
export default Grid;
