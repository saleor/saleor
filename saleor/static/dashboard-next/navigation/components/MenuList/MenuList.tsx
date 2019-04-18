import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import IconButtonTableCell from "../../../components/IconButtonTableCell";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection, stopPropagation } from "../../../misc";
import { ListProps } from "../../../types";
import { MenuList_menus_edges_node } from "../../types/MenuList";

export interface MenuListProps extends ListProps {
  menus: MenuList_menus_edges_node[];
  onDelete: (id: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colItems: {
        width: 200
      },
      colTitle: {}
    },
    colItems: {
      textAlign: "right"
    },
    colTitle: {},
    row: {
      cursor: "pointer"
    }
  });
const MenuList = withStyles(styles, { name: "MenuList" })(
  ({
    classes,
    disabled,
    menus,
    onDelete,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo
  }: MenuListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox" />
            <TableCell className={classes.colTitle}>
              {i18n.t("Menu Title", { context: "object" })}
            </TableCell>
            <TableCell className={classes.colItems}>
              {i18n.t("Items", { context: "number of menu items" })}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            menus,
            menu => (
              <TableRow
                hover={!!menu}
                key={menu ? menu.id : "skeleton"}
                onClick={menu && onRowClick(menu.id)}
                className={classes.row}
              >
                <TableCell>
                  <Checkbox />
                </TableCell>
                <TableCell className={classes.colTitle}>
                  {maybe<React.ReactNode>(() => menu.name, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.colItems}>
                  {maybe<React.ReactNode>(
                    () => menu.items.length,
                    <Skeleton />
                  )}
                </TableCell>
                <IconButtonTableCell
                  disabled={disabled}
                  onClick={() => onDelete(menu.id)}
                >
                  <DeleteIcon />
                </IconButtonTableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={4}>{i18n.t("No menus found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
MenuList.displayName = "MenuList";
export default MenuList;
