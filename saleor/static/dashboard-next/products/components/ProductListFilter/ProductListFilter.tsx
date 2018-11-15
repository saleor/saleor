import * as React from "react";

import {
  Filter,
  FilterChips,
  FilterTab,
  FilterTabs
} from "../../../components/TableFilter";
import i18n from "../../../i18n";

export type ProductListFilterTabs =
  | "all"
  | "available"
  | "outOfStock"
  | "custom";

interface ProductListFilterProps {
  currentTab: ProductListFilterTabs;
  filtersList: Filter[];
  onAllProducts: () => void;
  onAvailable: () => void;
  onOfStock: () => void;
  onCustomFilter: () => void;
}

const ProductListFilter: React.StatelessComponent<ProductListFilterProps> = ({
  filtersList,
  currentTab,
  onAllProducts,
  onAvailable,
  onOfStock,
  onCustomFilter
}) => (
  <>
    <FilterTabs
      currentTab={["all", "available", "outOfStock", "custom"].indexOf(
        currentTab
      )}
    >
      <FilterTab label={i18n.t("All Products")} onClick={onAllProducts} />
      <FilterTab label={i18n.t("Available")} onClick={onAvailable} />
      <FilterTab label={i18n.t("Out Of Stock")} onClick={onOfStock} />
      {currentTab === "custom" && filtersList && filtersList.length > 0 && (
        <FilterTab
          onClick={onCustomFilter}
          value={0}
          label={i18n.t("Custom Filter")}
        />
      )}
    </FilterTabs>
    {currentTab === "custom" && filtersList && filtersList.length > 0 && (
      <FilterChips filtersList={filtersList} />
    )}
  </>
);
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
