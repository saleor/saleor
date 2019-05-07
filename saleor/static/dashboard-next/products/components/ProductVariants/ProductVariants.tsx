import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Checkbox from "@material-ui/core/Checkbox";
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
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";
import { ListActions } from "../../../types";
import { ProductDetails_product_variants } from "../../types/ProductDetails";
import { ProductVariant_costPrice } from "../../types/ProductVariant";

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colName: {},
      colPrice: {
        width: 200
      },
      colSku: {
        width: 250
      },
      colStatus: {
        width: 200
      }
    },
    colName: {},
    colPrice: {
      textAlign: "right"
    },
    colSku: {},
    colStatus: {},
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

interface ProductVariantsProps extends ListActions, WithStyles<typeof styles> {
  disabled: boolean;
  variants: ProductDetails_product_variants[];
  fallbackPrice?: ProductVariant_costPrice;
  onAttributesEdit: () => void;
  onRowClick: (id: string) => () => void;
  onVariantAdd?();
}

export const ProductVariants = withStyles(styles, { name: "ProductVariants" })(
  ({
    classes,
    disabled,
    variants,
    fallbackPrice,
    onAttributesEdit,
    onRowClick,
    onVariantAdd,
    isChecked,
    selected,
    toggle,
    toolbar
  }: ProductVariantsProps) => (
    <Card>
      <CardTitle
        title={i18n.t("Variants")}
        toolbar={
          <>
            <Button onClick={onAttributesEdit} variant="text" color="primary">
              {i18n.t("Edit attributes")}
            </Button>
            <Button onClick={onVariantAdd} variant="text" color="primary">
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
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colName}>{i18n.t("Name")}</TableCell>
            <TableCell className={classes.colStatus}>
              {i18n.t("Status")}
            </TableCell>
            <TableCell className={classes.colSku}>{i18n.t("SKU")}</TableCell>
            <Hidden smDown>
              <TableCell className={classes.colPrice}>
                {i18n.t("Price")}
              </TableCell>
            </Hidden>
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            variants,
            variant => {
              const isSelected = variant ? isChecked(variant.id) : false;

              return (
                <TableRow
                  selected={isSelected}
                  hover={!!variant}
                  onClick={onRowClick(variant.id)}
                  key={variant ? variant.id : "skeleton"}
                  className={classes.link}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(variant.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colName}>
                    {variant ? variant.name || variant.sku : <Skeleton />}
                  </TableCell>
                  <TableCell className={classes.colStatus}>
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
                  <TableCell className={classes.colSku}>
                    {variant ? variant.sku : <Skeleton />}
                  </TableCell>
                  <Hidden smDown>
                    <TableCell className={classes.colPrice}>
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
              );
            },
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
