import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import * as classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface ProductVariantNavigationProps {
  current?: string;
  variants?: Array<{
    id: string;
    name: string;
    sku: string;
    image?: {
      edges?: Array<{
        node?: {
          url: string;
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
          {renderCollection(
            variants,
            variant => (
              <TableRow
                hover={!!variant}
                key={variant ? variant.id : "skeleton"}
                className={classes.link}
                onClick={variant ? () => onRowClick(variant.id) : undefined}
              >
                <TableCellAvatar
                  className={classNames({
                    [classes.tabActive]: variant && variant.id === current
                  })}
                  thumbnail={
                    variant &&
                    variant.image &&
                    variant.image.edges !== undefined
                      ? variant.image.edges.length > 0
                        ? variant.image.edges[0] &&
                          variant.image.edges[0].node &&
                          variant.image.edges[0].node.url
                        : null
                      : undefined
                  }
                />
                <TableCell className={classes.textLeft}>
                  {variant ? variant.name || variant.sku : <Skeleton />}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell>{i18n.t("This product has no variants")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductVariantNavigation.displayName = "ProductVariantNavigation";
export default ProductVariantNavigation;
