import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import SingleAutocompleteSelectField from "@saleor/components/SingleAutocompleteSelectField";
import { ProductTypeDetails_taxTypes } from "@saleor/productTypes/types/ProductTypeDetails";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ProductTypeForm } from "../ProductTypeDetailsPage/ProductTypeDetailsPage";

interface ProductTypeTaxesProps extends WithStyles<typeof styles> {
  data: {
    taxType: string;
  };
  taxTypeDisplayName: string;
  taxTypes: ProductTypeDetails_taxTypes[];
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = createStyles({
  root: {
    overflow: "visible"
  }
});

const ProductTypeTaxes = withStyles(styles, { name: "ProductTypeTaxes" })(
  ({
    classes,
    data,
    disabled,
    taxTypes,
    taxTypeDisplayName,
    onChange
  }: ProductTypeTaxesProps) => (
    <Card className={classes.root}>
      <CardTitle title={i18n.t("Taxes")} />
      <CardContent>
        <SingleAutocompleteSelectField
          disabled={disabled}
          displayValue={taxTypeDisplayName}
          label={i18n.t("Taxes")}
          name={"taxType" as keyof ProductTypeForm}
          onChange={onChange}
          value={data.taxType}
          choices={maybe(
            () =>
              taxTypes.map(c => ({ label: c.description, value: c.taxCode })),
            []
          )}
          InputProps={{
            autoComplete: "off"
          }}
        />
      </CardContent>
    </Card>
  )
);
ProductTypeTaxes.displayName = "ProductTypeTaxes";
export default ProductTypeTaxes;
