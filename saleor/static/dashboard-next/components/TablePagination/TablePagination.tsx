// @inheritedComponent TableCell

import { IconButtonProps } from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import Toolbar from "@material-ui/core/Toolbar";
import * as React from "react";

import TablePaginationActions from "./TablePaginationActions";

const styles = (theme: Theme) =>
  createStyles({
    actions: {
      color: theme.palette.text.secondary,
      flexShrink: 0,
      marginLeft: theme.spacing.unit * 2.5
    },
    caption: {
      flexShrink: 0
    },
    input: {
      flexShrink: 0,
      fontSize: "inherit"
    },
    root: {
      "&:last-child": {
        padding: 0
      }
    },
    select: {
      paddingLeft: theme.spacing.unit,
      paddingRight: theme.spacing.unit * 2
    },
    selectIcon: {
      top: 1
    },
    selectRoot: {
      color: theme.palette.text.secondary,
      marginLeft: theme.spacing.unit,
      marginRight: theme.spacing.unit * 4
    },
    spacer: {
      flex: "1 1 100%"
    },
    toolbar: {
      height: 56,
      minHeight: 56,
      paddingRight: 2
    }
  });

interface TablePaginationProps extends WithStyles<typeof styles> {
  Actions?: typeof TablePaginationActions;
  backIconButtonProps?: Partial<IconButtonProps>;
  colSpan: number;
  component?: string | typeof TableCell;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextIconButtonProps?: Partial<IconButtonProps>;
  onNextPage(event);
  onPreviousPage(event);
}

const TablePagination = withStyles(styles, { name: "TablePagination" })(
  ({
    Actions,
    backIconButtonProps,
    classes,
    colSpan: colSpanProp,
    component: Component,
    hasNextPage,
    hasPreviousPage,
    nextIconButtonProps,
    onNextPage,
    onPreviousPage,
    ...other
  }: TablePaginationProps) => {
    let colSpan;

    if (Component === TableCell || Component === "td") {
      colSpan = colSpanProp || 1000;
    }

    return (
      <Component className={classes.root} colSpan={colSpan} {...other}>
        <Toolbar className={classes.toolbar}>
          <div className={classes.spacer} />
          <Actions
            backIconButtonProps={backIconButtonProps}
            hasNextPage={hasNextPage}
            hasPreviousPage={hasPreviousPage}
            nextIconButtonProps={nextIconButtonProps}
            onNextPage={onNextPage}
            onPreviousPage={onPreviousPage}
          />
        </Toolbar>
      </Component>
    );
  }
);
TablePagination.defaultProps = {
  Actions: TablePaginationActions,
  component: TableCell
};

TablePagination.displayName = "TablePagination";
export default TablePagination;
