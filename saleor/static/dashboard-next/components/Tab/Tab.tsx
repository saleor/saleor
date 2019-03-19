import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    active: {},
    root: {
      "&$active": {
        borderBottomColor: theme.palette.primary.main,
        color: theme.typography.body1.color
      },
      "&:focus": {
        color: theme.palette.primary.main
      },
      "&:hover": {
        color: theme.palette.primary.main
      },
      borderBottom: "1px solid transparent",
      color: theme.typography.caption.color,
      cursor: "pointer",
      display: "inline-block",
      fontWeight: theme.typography.fontWeightRegular,
      marginRight: theme.spacing.unit * 2,
      minWidth: 40,
      padding: `0 ${theme.spacing.unit}px`,
      transition: theme.transitions.duration.short + "ms"
    }
  });

interface TabProps<T> extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  isActive: boolean;
  changeTab: (index: T) => void;
}

export function Tab<T>(value: T) {
  return withStyles(styles, { name: "Tab" })(
    ({ classes, children, isActive, changeTab }: TabProps<T>) => (
      <Typography
        component="span"
        className={classNames({
          [classes.root]: true,
          [classes.active]: isActive
        })}
        onClick={() => changeTab(value)}
      >
        {children}
      </Typography>
    )
  );
}

export default Tab;
