import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import PriceField from "../../../components/PriceField";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    grid: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface ProductVariantPriceProps extends WithStyles<typeof styles> {
  currencySymbol?: string;
  priceOverride?: string;
  costPrice?: string;
  errors: { [key: string]: string };
  loading?: boolean;
  onChange(event: any);
}

const ProductVariantPrice = withStyles(styles, { name: "ProductVariantPrice" })(
  ({
    classes,
    currencySymbol,
    costPrice,
    errors,
    priceOverride,
    loading,
    onChange
  }: ProductVariantPriceProps) => (
    <Card>
      <CardTitle title={i18n.t("Pricing")} />
      <CardContent>
        <div className={classes.grid}>
          <div>
            <PriceField
              error={!!errors.price_override}
              name="priceOverride"
              label={i18n.t("Selling price override")}
              hint={
                errors.price_override
                  ? errors.price_override
                  : i18n.t("Optional")
              }
              value={priceOverride}
              currencySymbol={currencySymbol}
              onChange={onChange}
              disabled={loading}
            />
          </div>
          <div>
            <PriceField
              error={!!errors.cost_price}
              name="costPrice"
              label={i18n.t("Cost price override")}
              hint={errors.cost_price ? errors.cost_price : i18n.t("Optional")}
              value={costPrice}
              currencySymbol={currencySymbol}
              onChange={onChange}
              disabled={loading}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
ProductVariantPrice.displayName = "ProductVariantPrice";
export default ProductVariantPrice;
