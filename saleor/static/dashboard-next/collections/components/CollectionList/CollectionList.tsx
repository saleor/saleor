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
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { CollectionList_collections_edges_node } from "../../types/CollectionList";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colAvailability: {
        width: 240
      },
      colName: {},
      colProducts: {
        width: 240
      }
    },
    colAvailability: {},
    colName: {},
    colProducts: {
      textAlign: "center"
    },
    tableRow: {
      cursor: "pointer" as "pointer"
    }
  });

interface CollectionListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
  collections: CollectionList_collections_edges_node[];
}

const CollectionList = withStyles(styles, { name: "CollectionList" })(
  ({
    classes,
    collections,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    isChecked,
    selected,
    toggle,
    toolbar
  }: CollectionListProps) => (
    <Card>
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colName}>
              {i18n.t("Category Name", { context: "table cell" })}
            </TableCell>
            <TableCell className={classes.colProducts}>
              {i18n
                .t("No. Products", { context: "table cell" })
                .replace(" ", "\xa0")}
            </TableCell>
            <TableCell className={classes.colAvailability}>
              {i18n.t("Availability", { context: "table cell" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={5}
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
            collections,
            collection => {
              const isSelected = collection ? isChecked(collection.id) : false;
              return (
                <TableRow
                  className={classes.tableRow}
                  hover={!!collection}
                  onClick={collection ? onRowClick(collection.id) : undefined}
                  key={collection ? collection.id : "skeleton"}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(collection.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {maybe<React.ReactNode>(
                      () => collection.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colProducts}>
                    {maybe<React.ReactNode>(
                      () => collection.products.totalCount,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colAvailability}>
                    {maybe(
                      () => (
                        <StatusLabel
                          status={collection.isPublished ? "success" : "error"}
                          label={
                            collection.isPublished
                              ? i18n.t("Published")
                              : i18n.t("Not published")
                          }
                        />
                      ),
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No collections found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CollectionList.displayName = "CollectionList";
export default CollectionList;
