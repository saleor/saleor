import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    grid: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface ProductVariantStockProps extends WithStyles<typeof styles> {
  errors: {
    quantity?: string;
    sku?: string;
  };
  sku: string;
  quantity: number;
  stockAllocated?: number;
  loading?: boolean;
  onChange(event: any);
}

const ProductVariantStock = withStyles(styles, { name: "ProductVariantStock" })(
  ({
    classes,
    errors,
    sku,
    quantity,
    stockAllocated,
    loading,
    onChange
  }: ProductVariantStockProps) => (
    <Card>
      <CardTitle title={i18n.t("Stock")} />
      <CardContent>
        <div className={classes.grid}>
          <div>
            <TextField
              error={!!errors.quantity}
              name="quantity"
              value={quantity}
              label={i18n.t("Inventory")}
              helperText={
                errors.quantity
                  ? errors.quantity
                  : !!stockAllocated
                  ? i18n.t("Allocated: {{ quantity }}", {
                      context: "variant allocated stock",
                      quantity: stockAllocated
                    })
                  : undefined
              }
              onChange={onChange}
              disabled={loading}
              fullWidth
            />
          </div>
          <div>
            <TextField
              error={!!errors.sku}
              helperText={errors.sku}
              name="sku"
              value={sku}
              label={i18n.t("SKU (Stock Keeping Unit)")}
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
ProductVariantStock.displayName = "ProductVariantStock";
export default ProductVariantStock;
