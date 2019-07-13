import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import React from "react";

import { stopPropagation } from "../../misc";
import { ICONBUTTON_SIZE } from "../../theme";

export interface IconButtonTableCellProps {
  children: React.ReactNode;
  disabled?: boolean;
  onClick: () => void;
}

const styles = (theme: Theme) =>
  createStyles({
    root: {
      "&:last-child": {
        paddingRight: 0
      },
      paddingRight: 0,
      width: ICONBUTTON_SIZE + theme.spacing.unit / 2
    }
  });
const IconButtonTableCell = withStyles(styles, { name: "IconButtonTableCell" })(
  ({
    children,
    classes,
    disabled,
    onClick
  }: IconButtonTableCellProps & WithStyles<typeof styles>) => (
    <TableCell className={classes.root}>
      <IconButton
        color="primary"
        disabled={disabled}
        onClick={stopPropagation(onClick)}
      >
        {children}
      </IconButton>
    </TableCell>
  )
);
IconButtonTableCell.displayName = "IconButtonTableCell";
export default IconButtonTableCell;
