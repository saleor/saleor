import * as React from "react";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";

interface TabProps {
  isActive: boolean;
  value: number;
  changeTab: (index: number) => void;
}

const decorate = withStyles(theme => ({
  active: {},
  root: {
    "&$active": {
      borderBottomColor: theme.palette.primary.main
    },
    borderBottom: "1px solid transparent",
    display: "inline-block" as "inline-block",
    minWidth: 40,
    fontWeight: theme.typography.fontWeightRegular,
    marginRight: theme.spacing.unit * 4,
    cursor: "pointer",
    "&:hover": {
      color: "#5AB378"
    },
    "&:focus": {
      color: "#5AB378"
    }
  }
}));

export const Tab = decorate<TabProps>(
  ({ classes, children, isActive, value, changeTab }) => (
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

export default Tab;
