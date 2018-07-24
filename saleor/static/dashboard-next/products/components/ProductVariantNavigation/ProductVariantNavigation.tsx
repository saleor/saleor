import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";

interface ProductVariantNavigationProps {
  current: string;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    images?: {
      edges?: Array<{
        node?: {
          image;
        };
      }>;
    };
  }>;
  onRowClick: (variantId: string) => void;
}

const decorate = withStyles(theme => ({
  link: {
    cursor: "pointer"
  },
  tabActive: {
    "&:before": {
      background: theme.palette.primary.main,
      content: '""',
      height: "100%",
      left: 0,
      position: "absolute" as "absolute",
      top: 0,
      width: 2
    },
    position: "relative" as "relative"
  },
  textLeft: {
    textAlign: [["left"], "!important"] as any
  }
}));

const ProductVariantNavigation = decorate<ProductVariantNavigationProps>(
  ({ classes, current, variants, onRowClick }) => (
    <Card>
      <CardTitle title={i18n.t("Variants")} />
      <Table>
        <TableBody>
          {variants === undefined ? (
            <TableRow hover>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : variants.length > 0 ? (
            variants.map(variant => (
              <TableRow
                hover
                key={variant.id}
                className={classes.link}
                onClick={() => onRowClick(variant.id)}
              >
                <TableCellAvatar
                  className={
                    variant.id === current ? classes.tabActive : undefined
                  }
                  thumbnail={
                    variant &&
                    variant.images &&
                    variant.images.edges &&
                    variant.images.edges[0] &&
                    variant.images.edges[0].node &&
                    variant.images.edges[0].node.image
                      ? variant.images.edges[0].node.image
                      : null
                  }
                />
                <TableCell className={classes.textLeft}>
                  {variant.name || variant.sku}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow hover>
              <TableCell>{i18n.t("This product has no variants")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
export default ProductVariantNavigation;
