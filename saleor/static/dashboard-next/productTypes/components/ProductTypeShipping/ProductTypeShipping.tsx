import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import i18n from "../../../i18n";
import { WeightUnitsEnum } from "../../../types/globalTypes";

interface ProductTypeShippingProps {
  data: {
    isShippingRequired: boolean;
    weight: number | null;
  };
  defaultWeightUnit: WeightUnitsEnum;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ProductTypeShipping: React.StatelessComponent<
  ProductTypeShippingProps
> = ({ data, defaultWeightUnit, disabled, onChange }) => (
  <Card>
    <CardTitle title={i18n.t("Shipping")} />
    <CardContent>
      <ControlledCheckbox
        checked={data.isShippingRequired}
        disabled={disabled}
        label={i18n.t("Is this product shippable?")}
        name="isShippingRequired"
        onChange={onChange}
      />
      {data.isShippingRequired && (
        <TextField
          disabled={disabled}
          InputProps={{ endAdornment: defaultWeightUnit }}
          label={i18n.t("Weight")}
          name="weight"
          helperText={i18n.t(
            "Used to calculate rates for shipping for products of this product type, when specific weight is not given"
          )}
          type="number"
          value={data.weight}
          onChange={onChange}
        />
      )}
    </CardContent>
  </Card>
);

ProductTypeShipping.displayName = "ProductTypeShipping";
export default ProductTypeShipping;
