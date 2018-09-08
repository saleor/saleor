import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import PriceField from "../../../components/PriceField";
import i18n from "../../../i18n";

interface ProductVariantPriceProps {
  currencySymbol?: string;
  priceOverride?: string;
  costPrice?: string;
  errors: { [key: string]: string };
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  grid: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr"
  },
  root: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  }
}));
const ProductVariantPrice = decorate<ProductVariantPriceProps>(
  ({
    classes,
    currencySymbol,
    costPrice,
    errors,
    priceOverride,
    loading,
    onChange
  }) => (
    <Card className={classes.root}>
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
export default ProductVariantPrice;
