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
import { maybe } from "../../../misc";
import { ProductDetails_product } from "../../types/ProductDetails";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface ProductStockProps extends WithStyles<typeof styles> {
  data: {
    sku: string;
    stockQuantity: number;
  };
  disabled: boolean;
  errors: { [key: string]: string };
  product: ProductDetails_product;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ProductStock = withStyles(styles, { name: "ProductStock" })(
  ({ classes, data, disabled, product, onChange, errors }: ProductStockProps) => (
    <Card>
      <CardTitle title={i18n.t("Inventory")} />
      <CardContent>
        <div className={classes.root}>
          <TextField
            disabled={disabled}
            name="sku"
            label={i18n.t("SKU (Stock Keeping Unit)")}
            value={data.sku}
            onChange={onChange}
            error={!!errors.sku}
            helperText={errors.sku}
          />
          <TextField
            disabled={disabled}
            name="stockQuantity"
            label={i18n.t("Inventory")}
            value={data.stockQuantity}
            type="number"
            onChange={onChange}
            helperText={
              product
                ? i18n.t("Allocated: {{ quantity }}", {
                    quantity: maybe(() => product.variants[0].quantityAllocated)
                  })
                : undefined
            }
          />
        </div>
      </CardContent>
    </Card>
  )
);
ProductStock.displayName = "ProductStock";
export default ProductStock;
