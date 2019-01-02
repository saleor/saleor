import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Hidden from "@material-ui/core/Hidden";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";
import { ProductDetails_product_variants } from "../../types/ProductDetails";
import { ProductVariant_costPrice } from "../../types/ProductVariant";

const styles = (theme: Theme) =>
  createStyles({
    denseTable: {
      "& td, & th": {
        paddingRight: theme.spacing.unit * 3
      }
    },
    link: {
      cursor: "pointer"
    },
    textLeft: {
      textAlign: "left" as "left"
    },
    textRight: {
      textAlign: "right" as "right"
    }
  });

interface ProductVariantsProps extends WithStyles<typeof styles> {
  disabled?: boolean;
  variants: ProductDetails_product_variants[];
  fallbackPrice?: ProductVariant_costPrice;
  onAttributesEdit: () => void;
  onRowClick: (id: string) => () => void;
  onVariantAdd?();
}

export const ProductVariants = withStyles(styles, { name: "ProductVariants" })(
  ({
    classes,
    variants,
    fallbackPrice,
    onAttributesEdit,
    onRowClick,
    onVariantAdd
  }: ProductVariantsProps) => (
    <Card>
      <CardTitle
        title={i18n.t("Variants")}
        toolbar={
          <>
            <Button onClick={onAttributesEdit} variant="text" color="secondary">
              {i18n.t("Edit attributes")}
            </Button>
            <Button onClick={onVariantAdd} variant="text" color="secondary">
              {i18n.t("Add variant")}
            </Button>
          </>
        }
      />
      <CardContent>
        <Typography>
          {i18n.t(
            "Use variants for products that come in a variety of version for example different sizes or colors"
          )}
        </Typography>
      </CardContent>
      <Table className={classes.denseTable}>
        <TableHead>
          <TableRow>
            <TableCell className={classes.textLeft}>{i18n.t("Name")}</TableCell>
            <TableCell>{i18n.t("Status")}</TableCell>
            <TableCell>{i18n.t("SKU")}</TableCell>
            <Hidden smDown>
              <TableCell className={classes.textRight}>
                {i18n.t("Price")}
              </TableCell>
            </Hidden>
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            variants,
            variant => (
              <TableRow
                hover={!!variant}
                key={variant ? variant.id : "skeleton"}
              >
                <TableCell
                  className={classNames(classes.textLeft, classes.link)}
                  onClick={onRowClick(variant.id)}
                >
                  {variant ? variant.name || variant.sku : <Skeleton />}
                </TableCell>
                <TableCell>
                  {variant ? (
                    <StatusLabel
                      status={variant.stockQuantity > 0 ? "success" : "error"}
                      label={
                        variant.stockQuantity > 0
                          ? i18n.t("Available")
                          : i18n.t("Unavailable")
                      }
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>{variant ? variant.sku : <Skeleton />}</TableCell>
                <Hidden smDown>
                  <TableCell className={classes.textRight}>
                    {variant ? (
                      variant.priceOverride ? (
                        <Money money={variant.priceOverride} />
                      ) : fallbackPrice ? (
                        <Money money={fallbackPrice} />
                      ) : (
                        <Skeleton />
                      )
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </Hidden>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("This product has no variants")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductVariants.displayName = "ProductVariants";
export default ProductVariants;
