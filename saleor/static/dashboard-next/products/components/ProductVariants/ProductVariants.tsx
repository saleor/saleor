import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import green from "@material-ui/core/colors/green";
import red from "@material-ui/core/colors/red";
import Hidden from "@material-ui/core/Hidden";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Money from "../../../components/Money";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface MoneyType {
  amount: number;
  currency: string;
}
interface ProductVariantsProps {
  disabled?: boolean;
  variants?: Array<{
    id: string;
    sku: string;
    name: string;
    priceOverride: number;
    quantity: number;
    margin: number;
  }>;
  fallbackPrice?: MoneyType;
  fallbackGross?: string;
  onRowClick?(id: string);
  onVariantAdd?();
}

const decorate = withStyles(theme => {
  const dot = {
    borderRadius: "100%",
    display: "inline-block",
    height: theme.spacing.unit,
    marginRight: theme.spacing.unit,
    width: theme.spacing.unit
  };
  return {
    alignRightText: {
      textAlign: "right" as "right"
    },
    denseTable: {
      "& td, & th": {
        paddingRight: theme.spacing.unit * 3
      }
    },
    greenDot: {
      ...dot,
      backgroundColor: green[500]
    },
    link: {
      color: blue[500],
      cursor: "pointer"
    },
    redDot: {
      ...dot,
      backgroundColor: red[500]
    }
  };
});
export const ProductVariants = decorate<ProductVariantsProps>(
  ({
    classes,
    disabled,
    variants,
    fallbackPrice,
    fallbackGross,
    onRowClick,
    onVariantAdd
  }) => (
    <Card>
      <PageHeader title={i18n.t("Variants")}>
        {!!onVariantAdd && (
          <IconButton disabled={disabled} onClick={onVariantAdd}>
            <AddIcon />
          </IconButton>
        )}
      </PageHeader>
      <Table className={classes.denseTable}>
        <TableHead>
          <TableRow>
            <Hidden smDown>
              <TableCell>{i18n.t("SKU")}</TableCell>
            </Hidden>
            <TableCell>{i18n.t("Name")}</TableCell>
            <TableCell>{i18n.t("Status")}</TableCell>
            <Hidden smDown>
              <TableCell className={classes.alignRightText}>
                {i18n.t("Price")}
              </TableCell>
            </Hidden>
          </TableRow>
        </TableHead>
        <TableBody>
          {variants === undefined || variants === null ? (
            <TableRow>
              <Hidden smDown>
                <TableCell>
                  <Skeleton />
                </TableCell>
              </Hidden>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <Hidden smDown>
                <TableCell className={classes.alignRightText}>
                  <Skeleton />
                </TableCell>
              </Hidden>
            </TableRow>
          ) : variants.length > 0 ? (
            variants.map(variant => (
              <TableRow key={variant.id}>
                <Hidden smDown>
                  <TableCell>{variant.sku}</TableCell>
                </Hidden>
                <TableCell
                  className={onRowClick ? classes.link : ""}
                  onClick={onRowClick ? onRowClick(variant.id) : () => {}}
                >
                  {variant.name}
                </TableCell>
                <TableCell>
                  <span
                    className={
                      variant.quantity > 0 ? classes.greenDot : classes.redDot
                    }
                  />
                  {variant.quantity > 0
                    ? i18n.t("Available")
                    : i18n.t("Unavailable")}
                </TableCell>
                <Hidden smDown>
                  <TableCell className={classes.alignRightText}>
                    {variant && variant.priceOverride !== undefined ? (
                      <Money
                        amount={variant.priceOverride || fallbackPrice.amount}
                        currency={fallbackPrice.currency}
                      />
                    ) : (
                      <Skeleton />
                    )}
                  </TableCell>
                </Hidden>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={2}>
                {i18n.t("This product has no variants")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
ProductVariants.displayName = "ProductVariants";
export default ProductVariants;
