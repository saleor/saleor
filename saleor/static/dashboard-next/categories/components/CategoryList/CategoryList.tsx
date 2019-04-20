import Button from "@material-ui/core/Button";
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

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colName: {
        width: 840
      },
      colProducts: {
        width: 160
      },
      colSubcategories: {
        width: 160
      }
    },
    colName: {},
    colProducts: {
      textAlign: "center"
    },
    colSubcategories: {
      textAlign: "center"
    },
    tableRow: {
      cursor: "pointer"
    }
  });

interface CategoryListProps
  extends ListProps,
    ListActions,
    WithStyles<typeof styles> {
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
    isRoot,
    pageInfo,
    isChecked,
    selected,
    toggle,
    toolbar,
    onAdd,
    onNextPage,
    onPreviousPage,
    onRowClick
  }: CategoryListProps) => (
    <Card>
      {!isRoot && (
        <CardTitle
          title={i18n.t("All Subcategories")}
          toolbar={
            <Button color="primary" variant="text" onClick={onAdd}>
              {i18n.t("Add subcategory")}
            </Button>
          }
        />
      )}
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colName}>
              {i18n.t("Category Name", { context: "object" })}
            </TableCell>
            <TableCell className={classes.colSubcategories}>
              {i18n.t("Subcategories", { context: "object" })}
            </TableCell>
            <TableCell className={classes.colProducts}>
              {i18n
                .t("No. Products", { context: "object" })
                .replace(" ", "\xa0")}
            </TableCell>
          </TableRow>
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
            categories,
            category => {
              const isSelected = category ? isChecked(category.id) : false;

              return (
                <TableRow
                  className={classes.tableRow}
                  hover={!!category}
                  onClick={category ? onRowClick(category.id) : undefined}
                  key={category ? category.id : "skeleton"}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(category.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {category && category.name ? category.name : <Skeleton />}
                  </TableCell>
                  <TableCell className={classes.colSubcategories}>
                    {category &&
                    category.children &&
                    category.children.totalCount !== undefined ? (
                      category.children.totalCount
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                  <TableCell className={classes.colProducts}>
                    {category &&
                    category.products &&
                    category.products.totalCount !== undefined ? (
                      category.products.totalCount
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </TableRow>
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>
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
