import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
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
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableCellAvatar from "../../../components/TableCellAvatar";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, PageListProps } from "../../../types";
import { CollectionDetails_collection } from "../../types/CollectionDetails";

const styles = (theme: Theme) =>
  createStyles({
    iconCell: {
      "&:last-child": {
        paddingRight: 0
      },
      width: 48 + theme.spacing.unit / 2
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
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell />
            <TableCell>{i18n.t("Name", { context: "table header" })}</TableCell>
            <TableCell>{i18n.t("Type", { context: "table header" })}</TableCell>
            <TableCell>
              {i18n.t("Published", { context: "table header" })}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={6}
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
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(product.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCellAvatar
                    thumbnail={maybe(() => product.thumbnail.url)}
                  />
                  <TableCell>
                    {maybe<React.ReactNode>(() => product.name, <Skeleton />)}
                  </TableCell>
                  <TableCell>
                    {maybe<React.ReactNode>(
                      () => product.productType.name,
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell>
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
                  <TableCell className={classes.iconCell}>
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
                <TableCell colSpan={6}>{i18n.t("No products found")}</TableCell>
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
