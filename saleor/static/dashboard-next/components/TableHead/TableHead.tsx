import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import TableCell from "@material-ui/core/TableCell";
import MuiTableHead, {
  TableHeadProps as MuiTableHeadProps
} from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import { Node } from "../../types";

import i18n from "../../i18n";
import Checkbox from "../Checkbox";

export interface TableHeadProps extends MuiTableHeadProps {
  disabled: boolean;
  selected: number;
  items: Node[];
  toolbar: React.ReactNode | React.ReactNodeArray;
  toggleAll: (items: Node[], selected: number) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    cell: {
      padding: 0
    },
    checkboxSelected: {
      backgroundColor: fade(theme.palette.primary.main, 0.05)
    },
    container: {
      alignItems: "center",
      display: "flex",
      height: 47,
      marginRight: -theme.spacing.unit * 2
    },
    padding: {
      "&:last-child": {
        padding: 0
      }
    },
    root: {
      backgroundColor: fade(theme.palette.primary.main, 0.05),
      borderBottom: "1px solid rgba(224, 224, 224, 1)",
      paddingLeft: 0,
      paddingRight: 24
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

const TableHead = withStyles(styles, {
  name: "TableHead"
})(
  ({
    classes,
    children,
    disabled,
    items,
    selected,
    toggleAll,
    toolbar,
    ...muiTableHeadProps
  }: TableHeadProps & WithStyles<typeof styles>) => {
    const [isSelected, setSelected] = React.useState(false);
    return (
      <MuiTableHead {...muiTableHeadProps}>
        <TableRow>
          <TableCell
            padding="checkbox"
            className={classNames({
              [classes.checkboxSelected]: selected
            })}
          >
            <Checkbox
              checked={isSelected}
              disabled={disabled}
              onChange={event => {
                toggleAll(items, selected);
                setSelected(!isSelected);
                event.stopPropagation();
              }}
            />
          </TableCell>
          {selected ? (
            <>
              <TableCell className={classNames(classes.root)} colSpan={50}>
                <div className={classes.container}>
                  {selected && (
                    <Typography>
                      {i18n.t("Selected {{ number }} items", {
                        number: selected
                      })}
                    </Typography>
                  )}
                  <div className={classes.spacer} />
                  <div className={classes.toolbar}>{toolbar}</div>
                </div>
              </TableCell>
            </>
          ) : (
            children
          )}
        </TableRow>
      </MuiTableHead>
    );
  }
);
TableHead.displayName = "TableHead";
export default TableHead;
