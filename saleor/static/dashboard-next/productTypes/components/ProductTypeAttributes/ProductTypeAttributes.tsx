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
import { maybe, renderCollection } from "../../../misc";
import {
  ProductTypeDetails_productType_productAttributes_edges_node,
  ProductTypeDetails_productType_variantAttributes_edges_node
} from "../../types/ProductTypeDetails";

interface ProductTypeAttributesProps {
  attributes:
    | ProductTypeDetails_productType_productAttributes_edges_node[]
    | ProductTypeDetails_productType_variantAttributes_edges_node[];
  title: string;
}

const decorate = withStyles({
  link: {
    cursor: "pointer" as "pointer"
  },
  textLeft: {
    textAlign: "left" as "left"
  }
});
const ProductTypeAttributes = decorate<ProductTypeAttributesProps>(
  ({ attributes, classes, title }) => (
    <Card>
      <CardTitle title={title} />
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Attribute name")}</TableCell>
            <TableCell className={classes.textLeft}>
              {i18n.t("Values")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            attributes,
            attribute => (
              <TableRow
                className={!!attribute ? classes.link : undefined}
                hover={!!attribute}
                key={maybe(() => attribute.id)}
              >
                <TableCell>
                  {maybe(() => attribute.name) ? attribute.name : <Skeleton />}
                </TableCell>
                <TableCell className={classes.textLeft}>
                  {maybe(() => attribute.values) !== undefined ? (
                    attribute.values.map(value => value.name).join(", ")
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("No attributes found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductTypeAttributes.displayName = "ProductTypeAttributes";
export default ProductTypeAttributes;
