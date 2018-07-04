import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductVariantNavigationProps {
  current?: string;
  loading?: boolean;
  productId?: string;
  variants?: Array<{
    id: string;
    name: string;
  }>;
  onRowClick(variantId: string);
}

const decorate = withStyles(theme => ({
  card: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  link: {
    color: blue[500],
    cursor: "pointer"
  }
}));

const ProductVariantNavigation = decorate<ProductVariantNavigationProps>(
  ({ classes, current, loading, productId, variants, onRowClick }) => (
    <Card className={classes.card}>
      <PageHeader title={i18n.t("Variants")} />
      <Table>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : variants.length > 0 ? (
            variants.map(variant => (
              <TableRow key={variant.id}>
                <TableCell className={classes.link} onClick={() => onRowClick(variant.id)}>
                  {variant.name}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell>{i18n.t("This product has no variants")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
export default ProductVariantNavigation;
