import { Theme } from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import makeStyles from "@material-ui/styles/makeStyles";
import * as React from "react";
import { SortableHandle as SortableHandleHoc } from "react-sortable-hoc";

import Draggable from "@saleor/icons/Draggable";

const useStyles = makeStyles((theme: Theme) => ({
  columnDrag: {
    width: 48 + theme.spacing.unit * 1.5
  },
  dragIcon: {
    cursor: "grab"
  }
}));

const SortableHandle = SortableHandleHoc(() => {
  const classes = useStyles({});

  return (
    <TableCell className={classes.columnDrag}>
      <Draggable className={classes.dragIcon} />
    </TableCell>
  );
});

export default SortableHandle;
