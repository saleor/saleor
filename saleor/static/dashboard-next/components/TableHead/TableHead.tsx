import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import MuiTableHead, {
  TableHeadProps as MuiTableHeadProps
} from "@material-ui/core/TableHead";
import * as React from "react";
import { fade } from "@material-ui/core/styles/colorManipulator";
import TableActions from "../TableActions";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";

import Checkbox from "../Checkbox";
import i18n from "../../i18n";

export interface TableHeadProps extends MuiTableHeadProps {
  selected: number;
  toolbar: React.ReactNode | React.ReactNodeArray;
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
    padding: {
      "&:last-child": {
        padding: 0
      }
    },
    root: {
      backgroundColor: fade(theme.palette.primary.main, 0.05),
      paddingLeft: 12,
      paddingRight: 24,
      position: "absolute",
      width: "calc(100% - 72px)"
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
    children,
    classes,
    disabled,
    items,
    selected,
    tablebar,
    toggleAll,
    toolbar,
    ...muiTableHeadProps
  }: TableHeadProps & WithStyles<typeof styles>) => {
    const [isSelected, setSelected] = React.useState(false);
    return (
      <MuiTableHead {...muiTableHeadProps}>
        <TableRow>
          <TableCell padding="checkbox">
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
              <div className={classNames(classes.root)}>
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
              </div>
            </>
          ) : (
            tablebar
          )}
        </TableRow>
      </MuiTableHead>
    );
  }
);
TableHead.displayName = "TableHead";
export default TableHead;
