import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { ListProps } from "../..";
import TableCellAvatar from "../../components/TableCellAvatar";
import i18n from "../../i18n";
import { MoneyType } from "../../products";
import Money from "../Money";
import Skeleton from "../Skeleton";
import StatusLabel from "../StatusLabel";
import TablePagination from "../TablePagination";

const decorate = withStyles(theme => ({
  avatarCell: {
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: 0,
    width: theme.spacing.unit * 5
  },
  link: {
    cursor: "pointer" as "pointer"
  },
  textLeft: {
    textAlign: "left" as "left"
  }
}));

interface ProductListProps extends ListProps {
  products?: Array<{
    id: string;
    name: string;
    productType: {
      name: string;
    };
    thumbnailUrl: string;
    availability: {
      available: boolean;
    };
    price: MoneyType;
  }>;
}

export const ProductList = decorate<ProductListProps>(
  ({
    classes,
    disabled,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick,
    products
  }) => (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell />
          <TableCell className={classes.textLeft}>
            {i18n.t("Name", { context: "object" })}
          </TableCell>
          <TableCell>{i18n.t("Type", { context: "object" })}</TableCell>
          <TableCell>{i18n.t("Published", { context: "object" })}</TableCell>
          <TableCell>{i18n.t("Price", { context: "object" })}</TableCell>
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
        {products === undefined ? (
          <TableRow>
            <TableCellAvatar />
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
          </TableRow>
        ) : products !== null && products.length > 0 ? (
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
              <TableCell>
                {product.availability &&
                product.availability.available !== undefined ? (
                  <StatusLabel
                    label={
                      product.availability.available
                        ? i18n.t("Published")
                        : i18n.t("Not published")
                    }
                    status={
                      product.availability.available ? "success" : "error"
                    }
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell>
                {product.price &&
                product.price.amount !== undefined &&
                product.price.currency ? (
                  <Money
                    amount={product.price.amount}
                    currency={product.price.currency}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={5}>{i18n.t("No products found")}</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  )
);

export default ProductList;
