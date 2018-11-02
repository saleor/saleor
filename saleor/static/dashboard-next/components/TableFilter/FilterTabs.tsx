import { withStyles } from "@material-ui/core/styles";
import Tabs from "@material-ui/core/Tabs";
import * as React from "react";

interface FilterTabsProps {
  currentTab: number;
}

const decorate = withStyles(theme => ({
  tabsRoot: {
    borderBottom: "1px solid #e0e0e0",
    paddingLeft: `${theme.spacing.unit * 3}px`
  }
}));

export const FilterTabs = decorate<FilterTabsProps>(
  ({ classes, children, currentTab }) => (
    <Tabs
      className={classes.tabsRoot}
      value={currentTab}
      indicatorColor={"primary"}
    >
      {children}
    </Tabs>
  )
);

export default FilterTabs;
