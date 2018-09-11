import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import MultiAutocompleteSelectField from "../../../components/MultiAutocompleteSelectField";
import i18n from "../../../i18n";

interface ChoiceType {
  label: string;
  value: string;
}
interface ProductTypeDetailsProps {
  data?: {
    name: string;
    hasVariants: boolean;
    productAttributes: ChoiceType[];
    variantAttributes: ChoiceType[];
  };
  disabled: boolean;
  searchLoading: boolean;
  searchResults: Array<{
    id: string;
    name: string;
  }>;
  onAttributeSearch: (name: string) => void;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({
  root: {
    overflow: "visible" as "visible"
  }
});
const ProductTypeDetails = decorate<ProductTypeDetailsProps>(
  ({
    classes,
    data,
    disabled,
    searchLoading,
    searchResults,
    onAttributeSearch,
    onChange
  }) => (
    <Card className={classes.root}>
      <CardContent>
        <TextField
          disabled={disabled}
          fullWidth
          label={i18n.t("Name")}
          name="name"
          onChange={onChange}
          value={data.name}
        />
        <FormSpacer />
        <MultiAutocompleteSelectField
          choices={searchResults.map(s => ({ label: s.name, value: s.id }))}
          fetchChoices={onAttributeSearch}
          helperText={i18n.t("Optional")}
          label={i18n.t("Product attributes")}
          loading={searchLoading}
          name="productAttributes"
          onChange={onChange}
          value={data.productAttributes}
        />
        <FormSpacer />
        {data.hasVariants && (
          <MultiAutocompleteSelectField
            choices={searchResults.map(s => ({ label: s.name, value: s.id }))}
            fetchChoices={onAttributeSearch}
            helperText={i18n.t("Optional")}
            label={i18n.t("Variant attributes")}
            loading={searchLoading}
            name="variantAttributes"
            onChange={onChange}
            value={data.variantAttributes}
          />
        )}
      </CardContent>
    </Card>
  )
);
ProductTypeDetails.displayName = "ProductTypeDetails";
export default ProductTypeDetails;
