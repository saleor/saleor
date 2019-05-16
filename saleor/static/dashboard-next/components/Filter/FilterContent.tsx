import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import { Filter } from "./Filter";

export interface FilterContentProps {
  filters: Filter[];
}

const styles = (theme: Theme) => createStyles({});
const FilterContent = withStyles(styles, { name: "FilterContent" })(
  ({ classes }: FilterContentProps & WithStyles<typeof styles>) => <div />
);
FilterContent.displayName = "FilterContent";
export default FilterContent;
