import { Theme } from "@material-ui/core/styles";
import TableBody, { TableBodyProps } from "@material-ui/core/TableBody";
import makeStyles from "@material-ui/styles/makeStyles";
import * as React from "react";
import { SortableContainer } from "react-sortable-hoc";

import { ReorderAction } from "@saleor/types";

const InnerSortableTableBody = SortableContainer<TableBodyProps>(
  ({ children, ...props }) => <TableBody {...props}>{children}</TableBody>
);

export interface SortableTableBodyProps {
  onSortEnd: ReorderAction;
}

const useStyles = makeStyles((theme: Theme) => ({
  ghost: {
    "& td": {
      borderBottom: "none"
    },
    background: theme.palette.background.paper,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.overrides.MuiTableCell.root.fontSize,
    opacity: 0.5
  }
}));

const SortableTableBody: React.FC<
  TableBodyProps & SortableTableBodyProps
> = props => {
  const classes = useStyles({});

  return (
    <InnerSortableTableBody
      helperClass={classes.ghost}
      axis="y"
      lockAxis="y"
      useDragHandle
      {...props}
    />
  );
};

export default SortableTableBody;
