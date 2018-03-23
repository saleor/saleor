import IconButton from "material-ui/IconButton";
import KeyboardArrowLeft from "material-ui/internal/svg-icons/KeyboardArrowLeft";
import KeyboardArrowRight from "material-ui/internal/svg-icons/KeyboardArrowRight";
import { withStyles } from "material-ui/styles";
import * as React from "react";

const decorate = withStyles(
  theme => ({
    root: {
      color: theme.palette.text.secondary,
      flexShrink: 0,
      marginLeft: theme.spacing.unit * 2.5
    }
  }),
  {
    name: "MuiTablePaginationActions",
    withTheme: true
  }
);

interface TablePaginationActionsProps {
  backIconButtonProps: any;
  classes: any;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  nextIconButtonProps: any;
  onNextPage(event);
  onPreviousPage(event);
}

const TablePaginationActions = decorate<TablePaginationActionsProps>(
  ({
    backIconButtonProps,
    classes,
    hasNextPage,
    hasPreviousPage,
    nextIconButtonProps,
    onNextPage,
    onPreviousPage,
    theme,
    ...other
  }) => (
    <div className={classes.root} {...other}>
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

export default TablePaginationActions;
