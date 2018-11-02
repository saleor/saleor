import * as React from "react";

import {
  Filter,
  FilterChip,
  FilterTab,
  FilterTabs
} from "../../../components/TableFilter";
import i18n from "../../../i18n";

interface ProductListFilterProps {
  currentTab: number;
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
    <FilterTabs currentTab={currentTab}>
      <FilterTab label={i18n.t("All Products")} onClick={onAllProducts} />
      <FilterTab label={i18n.t("Availiable")} onClick={onAvailable} />
      <FilterTab label={i18n.t("Out Of Stock")} onClick={onOfStock} />
      {(currentTab === 0 || undefined) &&
        filtersList &&
        filtersList.length > 0 && (
          <FilterTab
            onClick={onCustomFilter}
            value={0}
            label={i18n.t("Custom Filter")}
          />
        )}
    </FilterTabs>
    {(currentTab === 0 || undefined) &&
      filtersList &&
      filtersList.length > 0 && <FilterChip filtersList={filtersList} />}
  </>
);
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
