import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { SaleDetails_sale } from "../../types/SaleDetails";

export interface SaleCollectionsProps extends ListProps {
  sale: SaleDetails_sale;
}

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  },
  wideColumn: {
    width: "60%"
  }
});
const SaleCollections = withStyles(styles, {
  name: "SaleCollections"
})(
  ({
    sale,
    classes,
    disabled,
    pageInfo,
    onRowClick,
    onPreviousPage,
    onNextPage
  }: SaleCollectionsProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle
        title={i18n.t("Collections assigned to {{ saleName }}", {
          saleName: maybe(() => sale.name)
        })}
        toolbar={
          <Button variant="flat" color="secondary">
            {i18n.t("Assign collections")}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Collection name")}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Products")}
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
            maybe(() => sale.collections.edges.map(edge => edge.node)),
            collection => (
              <TableRow
                hover={!!collection}
                key={collection ? collection.id : "skeleton"}
                onClick={collection && onRowClick(collection.id)}
                className={classes.tableRow}
              >
                <TableCell>
                  {maybe<React.ReactNode>(() => collection.name, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {maybe<React.ReactNode>(
                    () => collection.products.totalCount,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
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
SaleCollections.displayName = "SaleCollections";
export default SaleCollections;
