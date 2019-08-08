import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
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
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import StatusLabel from "@saleor/components/StatusLabel";
import TableCellAvatar, {
  AVATAR_MARGIN
} from "@saleor/components/TableCellAvatar";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, PageListProps } from "../../../types";
import { CollectionDetails_collection } from "../../types/CollectionDetails";

const styles = (theme: Theme) =>
  createStyles({
    colActions: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
    },
    colName: {
      width: "auto"
    },
    colNameLabel: {
      marginLeft: AVATAR_MARGIN
    },
    colPublished: {
      width: 200
    },
    colType: {
      width: 200
    },
    table: {
      tableLayout: "fixed"
    },
    tableRow: {
      cursor: "pointer"
    }
  });

export interface CollectionProductsProps
  extends PageListProps,
    ListActions,
    WithStyles<typeof styles> {
  collection: CollectionDetails_collection;
  onProductUnassign: (id: string, event: React.MouseEvent<any>) => void;
}

const numberOfColumns = 5;

const CollectionProducts = withStyles(styles, { name: "CollectionProducts" })(
  ({
    classes,
    collection,
    disabled,
    onAdd,
    onNextPage,
    onPreviousPage,
    onProductUnassign,
    onRowClick,
    pageInfo,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar
  }: CollectionProductsProps) => (
    <Card>
      <CardTitle
        title={
          !!collection ? (
            i18n.t("Products in {{ collectionName }}", {
              collectionName: collection.name
            })
          ) : (
            <Skeleton />
          )
        }
        toolbar={
          <Button
            disabled={disabled}
            variant="text"
            color="primary"
            onClick={onAdd}
          >
            {i18n.t("Assign product", {
              context: "button"
            })}
          </Button>
        }
      />
      <Table className={classes.table}>
        <TableHead
          colSpan={numberOfColumns}
          selected={selected}
          disabled={disabled}
          items={maybe(() => collection.products.edges.map(edge => edge.node))}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.colName}>
            <span className={classes.colNameLabel}>
              {i18n.t("Name", { context: "table header" })}
            </span>
          </TableCell>
          <TableCell className={classes.colType}>
            {i18n.t("Type", { context: "table header" })}
          </TableCell>
          <TableCell className={classes.colPublished}>
            {i18n.t("Published", { context: "table header" })}
          </TableCell>
          <TableCell className={classes.colActions} />
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={numberOfColumns}
              hasNextPage={maybe(() => pageInfo.hasNextPage)}
              onNextPage={onNextPage}
              hasPreviousPage={maybe(() => pageInfo.hasPreviousPage)}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            maybe(() => collection.products.edges.map(edge => edge.node)),
            product => {
              const isSelected = product ? isChecked(product.id) : false;

              return (
                <TableRow
                  className={classes.tableRow}
                  hover={!!product}
                  onClick={!!product ? onRowClick(product.id) : undefined}
                  key={product ? product.id : "skeleton"}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(product.id)}
                    />
                  </TableCell>
                  <TableCellAvatar
                    className={classes.colName}
                    thumbnail={maybe(() => product.thumbnail.url)}
                  >
                    {maybe<React.ReactNode>(() => product.name, <Skeleton />)}
                  </TableCellAvatar>
                  <TableCell className={classes.colType}>
                    {maybe<React.ReactNode>(
                      () => product.productType.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colPublished}>
                    {maybe(
                      () => (
                        <StatusLabel
                          label={
                            product.isPublished
                              ? i18n.t("Published")
                              : i18n.t("Not published")
                          }
                          status={product.isPublished ? "success" : "error"}
                        />
                      ),
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colActions}>
                    <IconButton
                      disabled={!product}
                      onClick={event => onProductUnassign(product.id, event)}
                    >
                      <DeleteIcon color="primary" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell />
                <TableCell colSpan={numberOfColumns}>
                  {i18n.t("No products found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CollectionProducts.displayName = "CollectionProducts";
export default CollectionProducts;
