import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import FormControl from "@material-ui/core/FormControl";
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Radio from "@material-ui/core/Radio";
import RadioGroup from "@material-ui/core/RadioGroup";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import { VoucherType } from "../..";
import CardTitle from "../../../components/CardTitle";
import ControlledCheckbox from "../../../components/ControlledCheckbox";
import FormSpacer from "../../../components/FormSpacer";
import PriceField from "../../../components/PriceField";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";

interface Choice {
  label: string;
  value: string;
}

const styles = (theme: Theme) =>
  createStyles({
    card: {
      overflow: "visible"
    },
    formControl: {
      margin: `0 ${theme.spacing.unit * 3}px`
    }
  });

interface VoucherPropertiesProps extends WithStyles<typeof styles> {
  voucher?: {
    id: string;
    type: VoucherType;
    product: {
      id: string;
      name: string;
    } | null;
    category: {
      id: string;
      name: string;
    } | null;
    applyTo: string | null;
    limit: { amount: number; currency: string } | null;
  };
  data?: {
    applyToShipping: Choice | null;
    applyToAll: boolean | null;
    type: VoucherType;
    limit: number | null;
    product: Choice | null;
    category: Choice | null;
  };
  disabled?: boolean;
  categorySearchResults?: Array<{
    id: string;
    name: string;
  }>;
  productSearchResults?: Array<{
    id: string;
    name: string;
  }>;
  shippingSearchResults?: Array<{
    label: string;
    code: string;
  }>;
  loadingCategories?: boolean;
  loadingProducts?: boolean;
  loadingShipping?: boolean;
  fetchCategories?();
  fetchProducts?();
  fetchShipping?();
  onChange?(event: React.ChangeEvent<any>);
}

const VoucherProperties = withStyles(styles, { name: "VoucherProperties" })(
  ({
    classes,
    data,
    disabled,
    fetchCategories,
    fetchProducts,
    fetchShipping,
    loadingCategories,
    loadingProducts,
    loadingShipping,
    productSearchResults,
    shippingSearchResults,
    onChange
  }: VoucherPropertiesProps) => (
    <Card classes={{ root: classes.card }}>
      <CardTitle title={i18n.t("Voucher type")} />
      <FormControl
        component="fieldset"
        required
        className={classes.formControl}
      >
        <RadioGroup name="type" value={data.type} onChange={onChange}>
          <FormControlLabel
            disabled={disabled}
            value="VALUE"
            control={<Radio />}
            label={i18n.t("Whole cart")}
          />
          <FormControlLabel
            disabled={disabled}
            value="SHIPPING"
            control={<Radio />}
            label={i18n.t("Shipping")}
          />
          <FormControlLabel
            disabled={disabled}
            value="PRODUCT"
            control={<Radio />}
            label={i18n.t("Product")}
          />
          <FormControlLabel
            disabled={disabled}
            value="CATEGORY"
            control={<Radio />}
            label={i18n.t("Category")}
          />
        </RadioGroup>
      </FormControl>
      <CardContent>
        {data.type === "VALUE" && (
          <PriceField
            disabled={disabled}
            hint={i18n.t("Optional")}
            label={i18n.t("Minimal cart value")}
            name="limit"
            onChange={onChange}
            value={data.limit}
          />
        )}
        {data.type === "SHIPPING" && (
          <>
            <SingleAutocompleteSelectField
              choices={
                shippingSearchResults
                  ? shippingSearchResults.map(s => ({
                      label: s.label,
                      value: s.code
                    }))
                  : []
              }
              fetchChoices={fetchShipping}
              label={i18n.t("Discounted shipping")}
              loading={loadingShipping}
              name="applyTo"
              onChange={onChange}
              value={data.applyToShipping}
            />
            <FormSpacer />
            <PriceField
              disabled={disabled}
              hint={i18n.t("Optional")}
              label={i18n.t("Minimal cart value")}
              name="limit"
              onChange={onChange}
              value={data.limit}
            />
          </>
        )}
        {data.type === "PRODUCT" && (
          <>
            <SingleAutocompleteSelectField
              choices={
                productSearchResults
                  ? productSearchResults.map(s => ({
                      label: s.name,
                      value: s.id
                    }))
                  : []
              }
              fetchChoices={fetchProducts}
              label={i18n.t("Discounted product")}
              loading={loadingProducts}
              name="product"
              onChange={onChange}
              value={data.product}
            />
            <FormSpacer />
            <ControlledCheckbox
              checked={data.applyToAll}
              onChange={onChange}
              label={i18n.t("Apply to whole cart")}
              name="applyToAll"
            />
          </>
        )}
        {data.type === "CATEGORY" && (
          <>
            <SingleAutocompleteSelectField
              choices={
                productSearchResults
                  ? productSearchResults.map(s => ({
                      label: s.name,
                      value: s.id
                    }))
                  : []
              }
              fetchChoices={fetchCategories}
              label={i18n.t("Discounted category")}
              loading={loadingCategories}
              name="category"
              onChange={onChange}
              value={data.category}
            />
            <FormSpacer />
            <ControlledCheckbox
              checked={data.applyToAll}
              onChange={onChange}
              label={i18n.t("Apply to whole cart")}
              name="applyToAll"
            />
          </>
        )}
      </CardContent>
    </Card>
  )
);
VoucherProperties.displayName = "VoucherProperties";
export default VoucherProperties;
