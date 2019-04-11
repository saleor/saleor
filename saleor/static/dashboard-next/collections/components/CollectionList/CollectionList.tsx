import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import IconButton from "@material-ui/core/IconButton";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import useBulkActions from "../../../hooks/useBulkActions";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActionProps, ListProps } from "../../../types";
import { CollectionList_collections_edges_node } from "../../types/CollectionList";

const styles = createStyles({
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

interface CollectionListProps
  extends ListProps,
    ListActionProps<"onBulkPublish" | "onBulkUnpublish" | "onBulkDelete">,
    WithStyles<typeof styles> {
  collections: CollectionList_collections_edges_node[];
}

const CollectionList = withStyles(styles, { name: "CollectionList" })(
  ({
    classes,
    collections,
    disabled,
    onBulkDelete,
    onBulkPublish,
    onBulkUnpublish,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo
  }: CollectionListProps) => {
    const { isMember, listElements, toggle } = useBulkActions(collections);

    return (
      <Card>
        <Table>
          <TableHead
            selected={listElements.length}
            toolbar={
              <>
                <Button
                  color="primary"
                  onClick={() => onBulkUnpublish(listElements)}
                >
                  {i18n.t("Unpublish")}
                </Button>
                <Button
                  color="primary"
                  onClick={() => onBulkPublish(listElements)}
                >
                  {i18n.t("Publish")}
                </Button>
                <IconButton
                  color="primary"
                  onClick={() => onBulkDelete(listElements)}
                >
                  <DeleteIcon />
                </IconButton>
              </>
            }
          >
            <TableRow>
              <TableCell />
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
                hasNextPage={
                  pageInfo && !disabled ? pageInfo.hasNextPage : false
                }
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
                const isSelected = collection ? isMember(collection.id) : false;
                return (
                  <TableRow
                    className={classes.tableRow}
                    hover={!!collection}
                    onClick={collection ? onRowClick(collection.id) : undefined}
                    key={collection ? collection.id : "skeleton"}
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
                    <TableCell>
                      {maybe<React.ReactNode>(
                        () => collection.name,
                        <Skeleton />
                      )}
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
                            status={
                              collection.isPublished ? "success" : "error"
                            }
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
    );
  }
);
CollectionList.displayName = "CollectionList";
export default CollectionList;
