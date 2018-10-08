import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { ListProps } from "../../..";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { AttributeType } from "../../../products";

interface ProductTypeListProps extends ListProps {
  productTypes?: Array<{
    id: string;
    name?: string;
    hasVariants?: boolean;
    productAttributes?: AttributeType[];
    variantAttributes?: AttributeType[];
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  }
}));
const ProductTypeList = decorate<ProductTypeListProps>(
  ({
    classes,
    disabled,
    productTypes,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>
              {i18n.t("Product attributes", { context: "object" })}
            </TableCell>
            <TableCell>
              {i18n.t("Variant attributes", { context: "object" })}
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
            productTypes,
            productType => (
              <TableRow key={productType ? productType.id : "skeleton"}>
                <TableCell
                  onClick={
                    productType && onRowClick && onRowClick(productType.id)
                  }
                  className={classes.link}
                >
                  {productType ? productType.name : <Skeleton />}
                </TableCell>
                <TableCell>
                  {maybe(() => productType.productAttributes) ? (
                    productType.productAttributes
                      .map(attribute => attribute.name)
                      .join(", ")
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {maybe(() => productType.hasVariants) !== undefined ? (
                    maybe(() => productType.variantAttributes) ? (
                      productType.variantAttributes.length > 0 ? (
                        productType.variantAttributes
                          .map(attribute => attribute.name)
                          .join(", ")
                      ) : (
                        "-"
                      )
                    ) : (
                      <Skeleton />
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No product types found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
