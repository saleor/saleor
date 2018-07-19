import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
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

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer"
  },
  textLeft: {
    textAlign: "left" as "left"
  }
}));

interface ProductListProps {
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

export const ProductList = decorate<ProductListProps>(
  ({
    classes,
    hasNextPage,
    hasPreviousPage,
    products,
    onAddProduct,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <CardTitle
        title={i18n.t("Products")}
        toolbar={
          <Button variant="flat" color="secondary" onClick={onAddProduct}>
            {i18n.t("Add product")}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
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
          {products === undefined || products === null ? (
            <TableRow>
              <TableCellAvatar />
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : products.length > 0 ? (
            products.map(product => (
              <TableRow key={product.id}>
                <TableCellAvatar thumbnail={product.thumbnailUrl} />
                <TableCell className={classes.textLeft}>
                  <span
                    onClick={onRowClick ? onRowClick(product.id) : undefined}
                    className={onRowClick ? classes.link : ""}
                  >
                    {product.name}
                  </span>
                </TableCell>
                <TableCell>{product.productType.name}</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>{i18n.t("No products found")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);

export default ProductList;
