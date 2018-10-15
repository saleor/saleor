import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface CategoryListProps {
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
  onRowClick?(id: string): () => void;
}

const decorate = withStyles({
  centerText: {
    textAlign: "center" as "center"
  },
  tableRow: {
    cursor: "pointer" as "pointer"
  },
  wideColumn: {
    width: "100%"
  }
});

const CategoryList = decorate<CategoryListProps>(
  ({ categories, classes, isRoot, onAdd, onRowClick }) => (
    <Card>
      {!isRoot && (
        <CardTitle
          title={i18n.t("All Subcategories")}
          toolbar={
            <Button color="secondary" variant="flat" onClick={onAdd}>
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
