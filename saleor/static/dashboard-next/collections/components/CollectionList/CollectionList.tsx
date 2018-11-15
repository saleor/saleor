import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { CollectionList_collections_edges_node } from "../../types/CollectionList";

interface CollectionListProps extends ListProps {
  collections: CollectionList_collections_edges_node[];
}

const decorate = withStyles({
  name: {
    width: "50%"
  },
  tableRow: {
    cursor: "pointer" as "pointer"
  },
  textCenter: {
    textAlign: "center" as "center"
  },
  textLeft: {
    textAlign: "left" as "left"
  }
});
const CollectionList = decorate<CollectionListProps>(
  ({
    classes,
    collections,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.name}>
              {i18n.t("Category Name", { context: "table cell" })}
            </TableCell>
            <TableCell className={classes.textCenter}>
              {i18n
                .t("No. Products", { context: "table cell" })
                .replace(" ", "\xa0")}
            </TableCell>
            <TableCell className={classes.textLeft}>
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
            collection => (
              <TableRow
                className={classes.tableRow}
                hover={!!collection}
                onClick={collection ? onRowClick(collection.id) : undefined}
                key={collection ? collection.id : "skeleton"}
              >
                <TableCell>
                  {maybe<React.ReactNode>(() => collection.name, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textCenter}>
                  {maybe<React.ReactNode>(
                    () => collection.products.totalCount,
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textLeft}>
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
            ),
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
