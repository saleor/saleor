import TableBody from "@material-ui/core/TableBody";
import * as React from "react";
import { SortableContainer } from "react-sortable-hoc";

interface SortableTableBodyProps {
  children: React.ReactNode | React.ReactNodeArray;
}

const SortableTableBody = SortableContainer<SortableTableBodyProps>(
  ({ children }) => <TableBody>{children}</TableBody>
);

export default SortableTableBody;
