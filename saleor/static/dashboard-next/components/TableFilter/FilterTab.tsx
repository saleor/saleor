import { withStyles } from "@material-ui/core/styles";
import Tab from "@material-ui/core/Tab";
import * as React from "react";

interface FilterTabProps {
  onClick: () => void;
  label: string;
  value?: number;
}

const decorate = withStyles(theme => ({
  tabLabel: {
    color: "#616161",
    fontSize: "0.875rem"
  },
  tabRoot: {
    minWidth: "80px",
    opacity: 1,
    paddingTop: `${theme.spacing.unit * 1}px`,
    textTransform: "initial" as "initial"
  }
}));

export const FilterTab = decorate<FilterTabProps>(
  ({ classes, onClick, label, value }) => (
    <Tab
      disableRipple
      label={label}
      classes={{ root: classes.tabRoot, label: classes.tabLabel }}
      onClick={onClick}
      value={value}
    />
  )
);

export default FilterTab;
