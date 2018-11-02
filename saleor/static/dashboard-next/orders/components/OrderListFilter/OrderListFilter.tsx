import * as React from "react";

import {
  Filter,
  FilterChip,
  FilterTab,
  FilterTabs
} from "../../../components/TableFilter";
import i18n from "../../../i18n";

interface OrderListFilterProps {
  currentTab: number;
  filtersList: Filter[];
  onAllProducts: () => void;
  onToFulfill: () => void;
  onToCapture: () => void;
  onCustomFilter: () => void;
}

const OrderListFilter: React.StatelessComponent<OrderListFilterProps> = ({
  filtersList,
  currentTab,
  onAllProducts,
  onToFulfill,
  onToCapture,
  onCustomFilter
}) => (
  <>
    <FilterTabs currentTab={currentTab}>
      <FilterTab label={i18n.t("All Products")} onClick={onAllProducts} />
      <FilterTab label={i18n.t("Ready to fulfill")} onClick={onToFulfill} />
      <FilterTab label={i18n.t("Ready to capture")} onClick={onToCapture} />
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
OrderListFilter.displayName = "OrderListFilter";
export default OrderListFilter;
