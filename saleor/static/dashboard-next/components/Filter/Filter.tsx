import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

export interface FilterProps {
  
}

const styles = (theme: Theme) => createStyles({
    
});
const Filter = withStyles(styles, { name: "Filter" })(
  ({ classes }: FilterProps & WithStyles<typeof styles>) => <div />
);
Filter.displayName = "Filter";
export default Filter;
