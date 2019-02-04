import { empty, only } from "../misc";
import { StockAvailability } from "../types/globalTypes";
import { ProductListFilterTabs } from "./components/ProductListFilter";
import { ProductListQueryParams } from "./views/ProductList";

export const getTabName = (
  qs: ProductListQueryParams
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
