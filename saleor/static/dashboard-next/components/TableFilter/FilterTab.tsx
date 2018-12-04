import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Tab from "@material-ui/core/Tab";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
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
  });

interface FilterTabProps extends WithStyles<typeof styles> {
  onClick: () => void;
  label: string;
  value?: number;
}

export const FilterTab = withStyles(styles, { name: "FilterTab" })(
  ({ classes, onClick, label, value }: FilterTabProps) => (
    <Tab
      disableRipple
      label={label}
      classes={{ root: classes.tabRoot, label: classes.tabLabel }}
      onClick={onClick}
      value={value}
    />
  )
);
FilterTab.displayName = "FilterTab";
export default FilterTab;
