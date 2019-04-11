import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";

export interface TableActionsProps {
  children: React.ReactNode;
  className?: string;
  selected?: number;
}

const styles = (theme: Theme) =>
  createStyles({
    cell: {
      padding: 0
    },
    container: {
      alignItems: "center",
      display: "flex",
      height: 56,
      marginRight: -theme.spacing.unit * 2
    },
    root: {
      backgroundColor: fade(theme.palette.primary.main, 0.05)
    },
    spacer: {
      flex: 1
    },
    toolbar: {
      "& > *": {
        marginLeft: theme.spacing.unit
      }
    }
  });
const TableActions = withStyles(styles, { name: "TableActions" })(
  ({
    classes,
    className,
    children,
    selected
  }: TableActionsProps & WithStyles<typeof styles>) => (
    <TableRow className={classNames(classes.root, className)}>
      <TableCell className={classes.cell} colSpan={9999}>
        <div className={classes.container}>
          {selected && (
            <Typography>
              {i18n.t("Selected {{ number }} items", {
                number: selected
              })}
            </Typography>
          )}
          <div className={classes.spacer} />
          <div className={classes.toolbar}>{children}</div>
        </div>
      </TableCell>
    </TableRow>
  )
);
TableActions.displayName = "TableActions";
export default TableActions;
