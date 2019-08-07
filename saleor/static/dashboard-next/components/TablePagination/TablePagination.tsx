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
import React from "react";

import RowNumberSelect from "@saleor/components/RowNumberSelect";
import { maybe } from "@saleor/misc";
import { ListSettings } from "../../types";
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
      paddingLeft: 2,
      paddingRight: 2
    }
  });

interface TablePaginationProps extends WithStyles<typeof styles> {
  Actions?: typeof TablePaginationActions;
  backIconButtonProps?: Partial<IconButtonProps>;
  colSpan: number;
  component?: string | typeof TableCell;
  settings?: ListSettings;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextIconButtonProps?: Partial<IconButtonProps>;
  onNextPage(event);
  onPreviousPage(event);
  onUpdateListSettings?(key: keyof ListSettings, value: any): void;
}

const TablePagination = withStyles(styles, { name: "TablePagination" })(
  ({
    Actions,
    backIconButtonProps,
    classes,
    colSpan: colSpanProp,
    component: Component,
    settings,
    hasNextPage,
    hasPreviousPage,
    nextIconButtonProps,
    onNextPage,
    onPreviousPage,
    onUpdateListSettings,
    ...other
  }: TablePaginationProps) => {
    let colSpan;

    if (Component === TableCell || Component === "td") {
      colSpan = colSpanProp || 1000;
    }

    return (
      <Component className={classes.root} colSpan={colSpan} {...other}>
        <Toolbar className={classes.toolbar}>
          <div className={classes.spacer}>
            {maybe(() => settings.rowNumber) && (
              <RowNumberSelect
                choices={[20, 30, 50, 100]}
                settings={settings}
                onChange={onUpdateListSettings}
              />
            )}
          </div>
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
