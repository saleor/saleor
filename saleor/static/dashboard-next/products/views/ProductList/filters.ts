import { FilterContentSubmitData } from "../../../components/Filter";
import { Filter } from "../../../components/TableFilter";
import i18n from "../../../i18n";
import {
  ProductFilterInput,
  StockAvailability
} from "../../../types/globalTypes";
import { ProductFilterKeys } from "../../components/ProductListFilter";
import { ProductListUrlFilters, ProductListUrlQueryParams } from "../../urls";

export const PRODUCT_FILTERS_KEY = "productFilters";

export interface UserFilter {
  name: string;
  data: ProductListUrlFilters;
}

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
    stockAvailability: params.status
  };
}

export function getActiveFilters(
  params: ProductListUrlQueryParams
): ProductListUrlFilters {
  return Object.keys(params)
    .filter(key =>
      ((["query", "status", "priceFrom", "priceTo", "isPublished"] as Array<
        keyof ProductListUrlFilters
      >) as string[]).includes(key)
    )
    .reduce((acc, key) => {
      acc[key] = params[key];
      return acc;
    }, {});
}

export function areFiltersApplied(params: ProductListUrlQueryParams): boolean {
  return Object.keys(getActiveFilters(params)).some(key => !!params[key]);
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

function exists(param: any): boolean {
  return param !== undefined && param !== null;
}

interface ProductListChipFormatData {
  currencySymbol: string;
  locale: string;
}
export function createFilterChips(
  filters: ProductListUrlFilters,
  formatData: ProductListChipFormatData,
  onClose: (filters: ProductListUrlFilters) => void
): Filter[] {
  let filterChips: Filter[] = [];

  if (exists(filters.priceFrom) || exists(filters.priceTo)) {
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
            onClose({
              ...filters,
              priceFrom: undefined,
              priceTo: undefined
            })
        }
      ];
    } else {
      if (exists(filters.priceFrom)) {
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
              onClose({
                ...filters,
                priceFrom: undefined
              })
          }
        ];
      }

      if (exists(filters.priceTo)) {
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
              onClose({
                ...filters,
                priceTo: undefined
              })
          }
        ];
      }
    }
  }

  if (exists(filters.status)) {
    filterChips = [
      ...filterChips,
      {
        label:
          filters.status === StockAvailability.IN_STOCK.toString()
            ? i18n.t("Available")
            : i18n.t("Out Of Stock"),
        onClick: () =>
          onClose({
            ...filters,
            status: undefined
          })
      }
    ];
  }

  if (exists(filters.isPublished)) {
    filterChips = [
      ...filterChips,
      {
        label:
          filters.isPublished === StockAvailability.IN_STOCK.toString()
            ? i18n.t("Published")
            : i18n.t("Hidden"),
        onClick: () =>
          onClose({
            ...filters,
            isPublished: undefined
          })
      }
    ];
  }

  return filterChips;
}

export function getFilterTabs(): UserFilter[] {
  return JSON.parse(localStorage.getItem(PRODUCT_FILTERS_KEY)) || [];
}

export function saveFilterTab(name: string, data: ProductListUrlFilters) {
  const userFilters = getFilterTabs();

  localStorage.setItem(
    PRODUCT_FILTERS_KEY,
    JSON.stringify([
      ...userFilters,
      {
        data,
        name
      }
    ])
  );
}

export function deleteFilterTab(id: number) {
  const userFilters = getFilterTabs();

  localStorage.setItem(
    PRODUCT_FILTERS_KEY,
    JSON.stringify([...userFilters.slice(0, id - 1), ...userFilters.slice(id)])
  );
}
