// @inheritedComponent TableCell

import * as React from "react";
import PropTypes from "prop-types";
import { TableCell, Typography, Toolbar, withStyles } from "material-ui";
import { TablePaginationActions } from "./TablePaginationActions";

const decorate = withStyles(
  theme => ({
    root: {
      "&:last-child": {
        padding: 0
      }
    },
    toolbar: {
      height: 56,
      minHeight: 56,
      paddingRight: 2
    },
    spacer: {
      flex: "1 1 100%"
    },
    caption: {
      flexShrink: 0
    },
    input: {
      fontSize: "inherit",
      flexShrink: 0
    },
    selectRoot: {
      marginRight: theme.spacing.unit * 4,
      marginLeft: theme.spacing.unit,
      color: theme.palette.text.secondary
    },
    select: {
      paddingLeft: theme.spacing.unit,
      paddingRight: theme.spacing.unit * 2
    },
    selectIcon: {
      top: 1
    },
    actions: {
      flexShrink: 0,
      color: theme.palette.text.secondary,
      marginLeft: theme.spacing.unit * 2.5
    }
  }),
  {
    name: "MuiTablePagination"
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

export const TablePagination = decorate<TablePaginationProps>(
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
