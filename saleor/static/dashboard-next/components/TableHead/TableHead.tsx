import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import MuiTableHead, {
  TableHeadProps as MuiTableHeadProps
} from "@material-ui/core/TableHead";
import * as React from "react";

import TableActions from "../TableActions";

export interface TableHeadProps extends MuiTableHeadProps {
  selected: number;
  toolbar: React.ReactNode | React.ReactNodeArray;
}

const styles = createStyles({
  shrink: {}
});

const TableHead = withStyles(styles, {
  name: "TableHead"
})(
  ({
    children,
    classes,
    selected,
    toolbar,
    ...muiTableHeadProps
  }: TableHeadProps & WithStyles<typeof styles>) => (
    <MuiTableHead {...muiTableHeadProps}>
      {selected ? (
        <TableActions selected={selected}>{toolbar}</TableActions>
      ) : (
        children
      )}
    </MuiTableHead>
  )
);
TableHead.displayName = "TableHead";
export default TableHead;
