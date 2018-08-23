import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

interface ProductStockProps {
  data: {
    sku: string;
    stockQuantity: number;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "1fr 1fr"
  }
}));
const ProductStock = decorate<ProductStockProps>(
  ({ classes, data, disabled, onChange }) => (
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
          />
          <TextField
            disabled={disabled}
            name="stockInventory"
            label={i18n.t("Inventory")}
            value={data.stockQuantity}
            type="number"
            onChange={onChange}
          />
        </div>
      </CardContent>
    </Card>
  )
);
ProductStock.displayName = "ProductStock";
export default ProductStock;
