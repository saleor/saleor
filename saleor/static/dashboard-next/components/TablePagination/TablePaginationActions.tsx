import IconButton from "@material-ui/core/IconButton";
import KeyboardArrowLeft from "@material-ui/core/internal/svg-icons/KeyboardArrowLeft";
import KeyboardArrowRight from "@material-ui/core/internal/svg-icons/KeyboardArrowRight";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      color: theme.palette.text.secondary,
      flexShrink: 0,
      marginLeft: theme.spacing.unit * 2.5
    }
  });

export interface TablePaginationActionsProps
  extends WithStyles<typeof styles, true> {
  backIconButtonProps?: any;
  classes: any;
  className?: string;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextIconButtonProps?: any;
  onNextPage(event);
  onPreviousPage(event);
}

export const TablePaginationActions = withStyles(styles, {
  name: "TablePaginationActions",
  withTheme: true
})(
  ({
    backIconButtonProps,
    classes,
    className,
    hasNextPage,
    hasPreviousPage,
    nextIconButtonProps,
    onNextPage,
    onPreviousPage,
    theme,
    ...other
  }: TablePaginationActionsProps) => (
    <div className={classNames(classes.root, className)} {...other}>
      <IconButton
        onClick={onPreviousPage}
        disabled={!hasPreviousPage}
        {...backIconButtonProps}
      >
        {theme.direction === "rtl" ? (
          <KeyboardArrowRight />
        ) : (
          <KeyboardArrowLeft />
        )}
      </IconButton>
      <IconButton
        onClick={onNextPage}
        disabled={!hasNextPage}
        {...nextIconButtonProps}
      >
        {theme.direction === "rtl" ? (
          <KeyboardArrowLeft />
        ) : (
          <KeyboardArrowRight />
        )}
      </IconButton>
    </div>
  )
);

TablePaginationActions.displayName = "TablePaginationActions";
export default TablePaginationActions;
