import { empty, only } from "../misc";
import { StockAvailability } from "../types/globalTypes";
import { ProductListFilterTabs } from "./components/ProductListFilter";
import { ProductListUrlQueryParams } from "./urls";

export const getTabName = (
  qs: ProductListUrlQueryParams
): ProductListFilterTabs => {
  const filters = {
    status: qs.status
  };
  if (empty(filters)) {
    return "all";
  }
  if (only(filters, "status")) {
    return filters.status === StockAvailability.IN_STOCK
      ? "available"
      : "outOfStock";
  }
  return "custom";
};
