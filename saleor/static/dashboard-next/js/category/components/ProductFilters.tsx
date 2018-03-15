import * as React from "react";
import TextField from "material-ui/TextField";

import FilterCard, { FilterCardProps } from "../../components/cards/FilterCard";
import i18n from "../../i18n";

export const ProductFilters: React.StatelessComponent<FilterCardProps> = ({
  handleClear,
  handleSubmit
}) => (
  <FilterCard handleClear={handleClear} handleSubmit={handleSubmit}>
    <TextField
      fullWidth
      name="name"
      label={i18n.t("Name", { context: "object" })}
    />
  </FilterCard>
);

export default ProductFilters;
