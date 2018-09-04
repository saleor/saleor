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
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface CollectionProductsProps {
  disabled?: boolean;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  products: Array<{
    id: string;
    name: string;
    sku: string;
    availability: {
      available: boolean;
    };
  }>;
  onNextPage();
  onPreviousPage();
  onProductAdd?();
  onProductClick?(id: string): () => void;
  onProductRemove?(id: string): () => void;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  },
  root: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginTop: theme.spacing.unit
    }
  }
}));
const CollectionProducts = decorate<CollectionProductsProps>(
  ({
    classes,
    disabled,
    pageInfo,
    products,
    onProductAdd,
    onNextPage,
    onPreviousPage,
    onProductClick
  }) => (
    <Card className={classes.root}>
      <CardTitle
        title={i18n.t("Products")}
        toolbar={
          <Button
            color="secondary"
            variant="flat"
            disabled={disabled}
            onClick={onProductAdd}
          >
            {i18n.t("Add product")}
          </Button>
        }
      />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("SKU", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Status", { context: "object" })}</TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={pageInfo ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={pageInfo ? pageInfo.hasPreviousPage : false}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            products,
            product => (
              <TableRow key={product ? product.id : "skeleton"}>
                <TableCell
                  onClick={
                    product && onProductClick && onProductClick(product.id)
                  }
                  className={classes.link}
                >
                  {product ? product.name : <Skeleton />}
                </TableCell>
                <TableCell>{product ? product.sku : <Skeleton />}</TableCell>
                <TableCell>
                  {product ? (
                    <StatusLabel
                      status={
                        product.availability && product.availability.available
                          ? "success"
                          : "error"
                      }
                      label={
                        product.availability && product.availability.available
                          ? i18n.t("Published")
                          : i18n.t("Not published")
                      }
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("This collection has no products")}
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
