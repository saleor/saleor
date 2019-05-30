import { FilterContentSubmitData } from "../../../components/Filter";
import { ProductFilterInput } from "../../../types/globalTypes";
import { ProductFilterKeys } from "../../components/ProductListFilter";
import { ProductListUrlFilters, ProductListUrlQueryParams } from "../../urls";

export function getFilterVariables(
  params: ProductListUrlFilters
): ProductFilterInput {
  return {
    isPublished: params.isPublished,
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
      isPublished: filter.value === "true"
    };
  }
}
