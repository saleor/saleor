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

interface AttributeType {
  id: string;
  sortNumber?: number;
  name?: string;
}
interface AttributeEdgeType {
  node: AttributeType;
}
interface ProductTypeListProps extends ListProps {
  productTypes?: Array<{
    id: string;
    name?: string;
    hasVariants?: boolean;
    productAttributes?: {
      edges: AttributeEdgeType[];
    };
    variantAttributes?: {
      edges: AttributeEdgeType[];
    };
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
          {productTypes === undefined ? (
            <TableRow>
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
          ) : productTypes.length > 0 ? (
            productTypes.map(productType => (
              <TableRow key={productType.id}>
                <TableCell
                  onClick={
                    !!onRowClick ? onRowClick(productType.id) : undefined
                  }
                  className={!!onRowClick ? classes.link : ""}
                >
                  {productType.name}
                </TableCell>
                <TableCell>
                  {productType &&
                  productType.productAttributes &&
                  productType.productAttributes.edges ? (
                    productType.productAttributes.edges
                      .map(edge => edge.node.name)
                      .join(", ")
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {productType &&
                  productType.hasVariants &&
                  productType.variantAttributes &&
                  productType.variantAttributes.edges ? (
                    productType.variantAttributes.edges
                      .map(edge => edge.node.name)
                      .join(", ")
                  ) : productType && productType.hasVariants === undefined ? (
                    <Skeleton />
                  ) : (
                    "-"
                  )}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>
                {i18n.t("No product types found")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
