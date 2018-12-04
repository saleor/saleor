// @inheritedComponent TableCell

import { withStyles } from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import Toolbar from "@material-ui/core/Toolbar";
import * as React from "react";

import TablePaginationActions from "./TablePaginationActions";

const decorate = withStyles(
  theme => ({
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
  }),
  {
    name: "TablePagination"
  }
);

interface TablePaginationProps {
  Actions?: string | React.ComponentType;
  backIconButtonProps?: any;
  colSpan: number;
  component?: string | React.ComponentType;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextIconButtonProps?: any;
  onNextPage(event);
  onPreviousPage(event);
}

const TablePagination = decorate<TablePaginationProps>(
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
  }) => {
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
