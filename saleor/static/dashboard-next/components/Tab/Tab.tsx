import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

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
    "&:focus": {
      color: "#5AB378"
    },
    "&:hover": {
      color: "#5AB378"
    },
    borderBottom: "1px solid transparent",
    cursor: "pointer",
    display: "inline-block" as "inline-block",
    fontWeight: theme.typography.fontWeightRegular,
    marginRight: theme.spacing.unit * 4,
    minWidth: 40
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

Tab.displayName = "Tab";
export default Tab;
