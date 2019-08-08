import TableRow, { TableRowProps } from "@material-ui/core/TableRow";
import * as React from "react";
import { SortableElement } from "react-sortable-hoc";
import SortableHandle from "./SortableHandle";

const SortableTableRow = SortableElement<TableRowProps>(
  ({ children, ...props }) => (
    <TableRow {...props}>
      <SortableHandle />
      {children}
    </TableRow>
  )
);

export default SortableTableRow;
