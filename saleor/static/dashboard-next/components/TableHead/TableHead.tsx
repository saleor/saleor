import MuiTableHead, {
  TableHeadProps as MuiTableHeadProps
} from "@material-ui/core/TableHead";
import * as React from "react";

import TableActions from "../TableActions";

export interface TableHeadProps extends MuiTableHeadProps {
  selected: number;
  toolbar: React.ReactNode | React.ReactNodeArray;
}

const TableHead: React.StatelessComponent<TableHeadProps> = ({
  children,
  selected,
  toolbar,
  ...muiTableHeadProps
}) => (
  <MuiTableHead {...muiTableHeadProps}>
    {selected ? (
      <TableActions selected={selected}>{toolbar}</TableActions>
    ) : (
      children
    )}
  </MuiTableHead>
);
TableHead.displayName = "TableHead";
export default TableHead;
