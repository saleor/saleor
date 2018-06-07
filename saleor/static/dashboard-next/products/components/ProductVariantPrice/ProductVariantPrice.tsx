import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { FormSpacer } from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import PriceField from "../../../components/PriceField";
import i18n from "../../../i18n";

interface ProductVariantPriceProps {
  currencySymbol?: string;
  priceOverride?: number;
  costPrice?: number;
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  root: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  grid: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr"
  }
}));
const ProductVariantPrice = decorate<ProductVariantPriceProps>(
  ({
    classes,
    currencySymbol,
    costPrice,
    priceOverride,
    loading,
    onChange
  }) => (
    <Card className={classes.root}>
      <PageHeader title={i18n.t("Pricing")} />
      <CardContent>
        <div className={classes.grid}>
          <div>
            <PriceField
              label={i18n.t("Selling price override")}
              hint={i18n.t("Optional")}
              value={priceOverride}
              currencySymbol={currencySymbol}
              onChange={onChange}
              disabled={loading}
            />
          </div>
          <div>
            <PriceField
              label={i18n.t("Cost price override")}
              hint={i18n.t("Optional")}
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
