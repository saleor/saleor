import * as React from "react";
import PropTypes from "prop-types";
import theme from "../theme";
import KeyboardArrowLeft from "material-ui/internal/svg-icons/KeyboardArrowLeft";
import KeyboardArrowRight from "material-ui/internal/svg-icons/KeyboardArrowRight";
import { IconButton, withStyles } from "material-ui";

const decorate = withStyles(
  theme => ({
    root: {
      flexShrink: 0,
      color: theme.palette.text.secondary,
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
  theme: any;
}

export const TablePaginationActions = decorate<TablePaginationActionsProps>(
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
