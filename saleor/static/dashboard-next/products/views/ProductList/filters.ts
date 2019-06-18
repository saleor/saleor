import { FilterContentSubmitData } from "../../../components/Filter";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import {
  ProductFilterInput,
  StockAvailability
} from "../../../types/globalTypes";
import {
  createFilterTabUtils,
  createFilterUtils
} from "../../../utils/filters";
import { ProductFilterKeys } from "../../components/ProductListFilter";
import {
  ProductListUrlFilters,
  ProductListUrlFiltersEnum,
  ProductListUrlQueryParams
} from "../../urls";

export const PRODUCT_FILTERS_KEY = "productFilters";

export function getFilterVariables(
  params: ProductListUrlFilters
): ProductFilterInput {
  return {
    isPublished:
      params.isPublished !== undefined ? params.isPublished === "true" : null,
    price: {
      gte: parseFloat(params.priceFrom),
      lte: parseFloat(params.priceTo)
    },
    search: params.query,
    stockAvailability: StockAvailability[params.status]
  };
}

export function createFilter(
  filter: FilterContentSubmitData
): ProductListUrlFilters {
  const filterName = filter.name;
  if (filterName === ProductFilterKeys.priceEqual.toString()) {
    const value = filter.value as string;
    return {
      priceFrom: value,
      priceTo: value
    };
  } else if (filterName === ProductFilterKeys.priceRange.toString()) {
    const { value } = filter;
    return {
      priceFrom: value[0],
      priceTo: value[1]
    };
  } else if (filterName === ProductFilterKeys.published.toString()) {
    return {
      isPublished: filter.value as string
    };
  } else if (filterName === ProductFilterKeys.stock.toString()) {
    const value = filter.value as string;
    return {
      status: StockAvailability[value]
    };
  }
}

interface ProductListChipFormatData {
  currencySymbol: string;
  locale: string;
}
export function createFilterChips(
  filters: ProductListUrlFilters,
  formatData: ProductListChipFormatData,
  onFilterDelete: (filters: ProductListUrlFilters) => void
): Filter[] {
  let filterChips: Filter[] = [];

  if (!!filters.priceFrom || !!filters.priceTo) {
    if (filters.priceFrom === filters.priceTo) {
      filterChips = [
        ...filterChips,
        {
          label: i18n.t("Price is {{ price }}", {
            price: parseFloat(filters.priceFrom).toLocaleString(
              formatData.locale,
              {
                currency: formatData.currencySymbol,
                style: "currency"
              }
            )
          }),
          onClick: () =>
            onFilterDelete({
              ...filters,
              priceFrom: undefined,
              priceTo: undefined
            })
        }
      ];
    } else {
      if (!!filters.priceFrom) {
        filterChips = [
          ...filterChips,
          {
            label: i18n.t("Price from {{ price }}", {
              price: parseFloat(filters.priceFrom).toLocaleString(
                formatData.locale,
                {
                  currency: formatData.currencySymbol,
                  style: "currency"
                }
              )
            }),
            onClick: () =>
              onFilterDelete({
                ...filters,
                priceFrom: undefined
              })
          }
        ];
      }

      if (!!filters.priceTo) {
        filterChips = [
          ...filterChips,
          {
            label: i18n.t("Price to {{ price }}", {
              price: parseFloat(filters.priceTo).toLocaleString(
                formatData.locale,
                {
                  currency: formatData.currencySymbol,
                  style: "currency"
                }
              )
            }),
            onClick: () =>
              onFilterDelete({
                ...filters,
                priceTo: undefined
              })
          }
        ];
      }
    }
  }

  if (!!filters.status) {
    filterChips = [
      ...filterChips,
      {
        label:
          filters.status === StockAvailability.IN_STOCK.toString()
            ? i18n.t("Available")
            : i18n.t("Out Of Stock"),
        onClick: () =>
          onFilterDelete({
            ...filters,
            status: undefined
          })
      }
    ];
  }

  if (!!filters.isPublished) {
    filterChips = [
      ...filterChips,
      {
        label:
          filters.isPublished === StockAvailability.IN_STOCK.toString()
            ? i18n.t("Published")
            : i18n.t("Hidden"),
        onClick: () =>
          onFilterDelete({
            ...filters,
            isPublished: undefined
          })
      }
    ];
  }

  return filterChips;
}

export const {
  deleteFilterTab,
  getFilterTabs,
  saveFilterTab
} = createFilterTabUtils<ProductListUrlFilters>(PRODUCT_FILTERS_KEY);

export const { areFiltersApplied, getActiveFilters } = createFilterUtils<
  ProductListUrlQueryParams,
  ProductListUrlFilters
>(ProductListUrlFiltersEnum);
