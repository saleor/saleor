import * as React from "react";
import TextField from "material-ui/TextField";

import FilterCard, { FilterCardProps } from "../../components/cards/FilterCard";

export const ProductFilters: React.StatelessComponent<FilterCardProps> = ({
  handleClear,
  handleSubmit
}) => (
  <FilterCard handleClear={handleClear} handleSubmit={handleSubmit}>
    <TextField fullWidth name="name" placeholder="Name" />
  </FilterCard>
);

export default ProductFilters;
