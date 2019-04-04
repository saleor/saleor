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
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TableCellAvatar from "../../../components/TableCellAvatar";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

const styles = (theme: Theme) =>
  createStyles({
    link: {
      color: theme.palette.primary.main,
      cursor: "pointer"
    },
    textLeft: {
      textAlign: "left"
    }
  });

interface ProductListProps extends WithStyles<typeof styles> {
  hasNextPage?: boolean;
  hasPreviousPage?: boolean;
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
  }>;
  onAddProduct?();
  onNextPage?();
  onPreviousPage?();
  onRowClick?(id: string): () => void;
}

export const ProductList = withStyles(styles, { name: "ProductList" })(
  ({
    classes,
    hasNextPage,
    hasPreviousPage,
    products,
    onAddProduct,
    onNextPage,
    onPreviousPage,
    onRowClick
  }: ProductListProps) => (
    <Card>
      <CardTitle
        title={i18n.t("Products")}
        toolbar={
          <Button variant="text" color="primary" onClick={onAddProduct}>
            {i18n.t("Add product")}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            {(products === undefined || products.length > 0) && <TableCell />}
            <TableCell className={classes.textLeft}>
              {i18n.t("Name", { context: "object" })}
            </TableCell>
            <TableCell>{i18n.t("Type", { context: "object" })}</TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={hasNextPage}
              onNextPage={onNextPage}
              hasPreviousPage={hasPreviousPage}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            products,
            product => (
              <TableRow key={product ? product.id : "skeleton"}>
                <TableCellAvatar thumbnail={product && product.thumbnailUrl} />
                <TableCell className={classes.textLeft}>
                  {product ? (
                    <span
                      onClick={onRowClick && onRowClick(product.id)}
                      className={classes.link}
                    >
                      {product.name}
                    </span>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {product && product.productType ? (
                    product.productType.name
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>{i18n.t("No products found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductList.displayName = "CategoryProductList";
export default ProductList;
