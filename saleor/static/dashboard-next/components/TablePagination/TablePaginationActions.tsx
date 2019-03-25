import IconButton from "@material-ui/core/IconButton";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import ArrowLeft from "@material-ui/icons/ArrowLeft";
import ArrowRight from "@material-ui/icons/ArrowRight";
import * as classNames from "classnames";
import * as React from "react";
import useTheme from "../../hooks/useTheme";

const styles = (theme: Theme) =>
  createStyles({
    dark: {
      "& svg": {
        color: theme.palette.primary.main
      },
      "&$disabled": {
        "& svg": {
          color: fade(theme.palette.primary.main, 0.2)
        }
      },
      "&:focus, &:hover": {
        "& > span:first-of-type": {
          backgroundColor: fade(theme.palette.primary.main, 0.2)
        }
      }
    },
    disabled: {},
    iconButton: {
      "& > span:first-of-type": {
        backgroundColor: theme.palette.background.default,
        borderRadius: "100%",
        transition: theme.transitions.duration.standard + "ms"
      },
      "&:focus, &:hover": {
        "& > span:first-of-type": {
          backgroundColor: fade(theme.palette.primary.main, 0.2)
        },
        backgroundColor: "transparent"
      }
    },
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
  }: TablePaginationActionsProps) => {
    const { isDark } = useTheme();
    return (
      <div className={classNames(classes.root, className)} {...other}>
        <IconButton
          className={classNames(classes.iconButton, {
            [classes.dark]: isDark,
            [classes.disabled]: !hasPreviousPage
          })}
          onClick={onPreviousPage}
          disabled={!hasPreviousPage}
          {...backIconButtonProps}
        >
          {theme.direction === "rtl" ? <ArrowRight /> : <ArrowLeft />}
        </IconButton>
        <IconButton
          className={classNames(classes.iconButton, {
            [classes.dark]: isDark,
            [classes.disabled]: !hasNextPage
          })}
          onClick={onNextPage}
          disabled={!hasNextPage}
          {...nextIconButtonProps}
        >
          {theme.direction === "rtl" ? <ArrowLeft /> : <ArrowRight />}
        </IconButton>
      </div>
    );
  }
);

TablePaginationActions.displayName = "TablePaginationActions";
export default TablePaginationActions;
