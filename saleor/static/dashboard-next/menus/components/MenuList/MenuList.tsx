import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { Menu } from "../..";
import { ListProps } from "../../../";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface MenuListProps extends ListProps {
  menus?: Array<
    Menu & {
      items: {
        totalCount: number;
      };
    }
  >;
}

const decorate = withStyles({
  row: {
    cursor: "pointer" as "pointer"
  },
  wideCell: {
    width: "100%"
  }
});
const MenuList = decorate<MenuListProps>(
  ({ classes, menus, pageInfo, onNextPage, onPreviousPage, onRowClick }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideCell}>{i18n.t("Name")}</TableCell>
            <TableCell>{i18n.t("Items")}</TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TablePagination
            colSpan={2}
            hasNextPage={pageInfo ? pageInfo.hasNextPage : undefined}
            onNextPage={onNextPage}
            hasPreviousPage={pageInfo ? pageInfo.hasPreviousPage : undefined}
            onPreviousPage={onPreviousPage}
          />
        </TableFooter>
        <TableBody>
          {renderCollection(
            menus,
            menu => (
              <TableRow
                className={classes.row}
                hover={true}
                onClick={menu && menu.id ? onRowClick(menu.id) : undefined}
                key={menu ? menu.id : "skeleton"}
              >
                <TableCell>
                  {menu && menu.name !== undefined ? menu.name : <Skeleton />}
                </TableCell>
                <TableCell>
                  {menu && menu.items && menu.items.totalCount !== undefined ? (
                    menu.items.totalCount
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>{i18n.t("No menus found")}</TableCell>
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
