import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { FormSpacer } from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface ProductVariantStockProps {
  sku?: string;
  stock?: number;
  stockAllocated?: number;
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
    gridTemplateColumns: "1fr 1fr",
    "& input": {
      width: "100%"
    }
  }
}));
const ProductVariantStock = decorate<ProductVariantStockProps>(
  ({ classes, sku, stock, stockAllocated, loading, onChange }) => (
    <Card className={classes.root}>
      <PageHeader title={i18n.t("Stock")} />
      <CardContent>
        <div className={classes.grid}>
          <div>
            <TextField
              name="stock"
              value={stock}
              label={i18n.t("In stock")}
              helperText={
                loading ? "" : `${i18n.t("Allocated:")} ${stockAllocated}`
              }
              onChange={onChange}
              disabled={loading}
              fullWidth
            />
          </div>
          <div>
            <TextField
              name="sku"
              value={sku}
              label={i18n.t("SKU")}
              onChange={onChange}
              disabled={loading}
              fullWidth
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
);
export default ProductVariantStock;
