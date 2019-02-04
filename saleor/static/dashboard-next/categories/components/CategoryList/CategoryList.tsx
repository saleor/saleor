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
import { renderCollection } from "../../../misc";
import { ListProps } from "../../../types";

const styles = createStyles({
  centerText: {
    textAlign: "center"
  },
  tableRow: {
    cursor: "pointer"
  },
  wideColumn: {
    width: "100%"
  }
});

interface CategoryListProps extends ListProps, WithStyles<typeof styles> {
  categories?: Array<{
    id: string;
    name: string;
    children: {
      totalCount: number;
    };
    products: {
      totalCount: number;
    };
  }>;
  isRoot: boolean;
  onAdd?();
}

const CategoryList = withStyles(styles, { name: "CategoryList" })(
  ({
    categories,
    classes,
    disabled,
    pageInfo,
    onNextPage,
    onPreviousPage,
    isRoot,
    onAdd,
    onRowClick
  }: CategoryListProps) => (
    <Card>
      {!isRoot && (
        <CardTitle
          title={i18n.t("All Subcategories")}
          toolbar={
            <Button color="secondary" variant="text" onClick={onAdd}>
              {i18n.t("Add subcategory")}
            </Button>
          }
        />
      )}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Category Name", { context: "object" })}
            </TableCell>
            <TableCell className={classes.centerText}>
              {i18n.t("Subcategories", { context: "object" })}
            </TableCell>
            <TableCell className={classes.centerText}>
              {i18n
                .t("No. Products", { context: "object" })
                .replace(" ", "\xa0")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
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
            categories,
            category => (
              <TableRow
                className={classes.tableRow}
                hover={!!category}
                onClick={category ? onRowClick(category.id) : undefined}
                key={category ? category.id : "skeleton"}
              >
                <TableCell>
                  {category && category.name ? category.name : <Skeleton />}
                </TableCell>
                <TableCell className={classes.centerText}>
                  {category &&
                  category.children &&
                  category.children.totalCount !== undefined ? (
                    category.children.totalCount
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.centerText}>
                  {category &&
                  category.products &&
                  category.products.totalCount !== undefined ? (
                    category.products.totalCount
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {isRoot
                    ? i18n.t("No categories found")
                    : i18n.t("No subcategories found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CategoryList.displayName = "CategoryList";
export default CategoryList;
