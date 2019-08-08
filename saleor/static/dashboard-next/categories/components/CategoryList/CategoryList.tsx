import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
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
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "@saleor/i18n";
import { renderCollection } from "@saleor/misc";
import { ListActions, ListProps } from "@saleor/types";

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
    colName: {
      paddingLeft: "0 !important"
    },
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

const numberOfColumns = 4;

const CategoryList = withStyles(styles, { name: "CategoryList" })(
  ({
    categories,
    classes,
    disabled,
    settings,
    isRoot,
    pageInfo,
    isChecked,
    selected,
    toggle,
    toggleAll,
    toolbar,
    onAdd,
    onNextPage,
    onPreviousPage,
    onUpdateListSettings,
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
        <TableHead
          colSpan={numberOfColumns}
          selected={selected}
          disabled={disabled}
          items={categories}
          toggleAll={toggleAll}
          toolbar={toolbar}
        >
          <TableCell className={classes.colName}>
            {i18n.t("Category Name", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colSubcategories}>
            {i18n.t("Subcategories", { context: "object" })}
          </TableCell>
          <TableCell className={classes.colProducts}>
            {i18n.t("No. Products", { context: "object" }).replace(" ", "\xa0")}
          </TableCell>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={numberOfColumns}
              settings={settings}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              onUpdateListSettings={onUpdateListSettings}
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
                      checked={isSelected}
                      disabled={disabled}
                      onChange={() => toggle(category.id)}
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
                <TableCell colSpan={numberOfColumns}>
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
