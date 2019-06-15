import Card from "@material-ui/core/Card";
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
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import Checkbox from "@saleor/components/Checkbox";
import IconButtonTableCell from "@saleor/components/IconButtonTableCell";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { MenuList_menus_edges_node } from "../../types/MenuList";

export interface MenuListProps extends ListProps, ListActions {
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
    isChecked,
    menus,
    onDelete,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    selected,
    toggle,
    toggleAll,
    toolbar
  }: MenuListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead
          selected={selected}
          disabled={disabled}
          items={menus}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.colTitle}>
            {i18n.t("Menu Title", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colItems}>
            {i18n.t("Items", { context: "number of menu items" })}
          </TableCell>
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
            menu => {
              const isSelected = menu ? isChecked(menu.id) : false;

              return (
                <TableRow
                  hover={!!menu}
                  key={menu ? menu.id : "skeleton"}
                  onClick={menu && onRowClick(menu.id)}
                  className={classes.row}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(menu.id)}
                    />
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
              );
            },
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
