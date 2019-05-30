import * as React from "react";

import Debounce from "../../../components/Debounce";
import { FilterContentSubmitData } from "../../../components/Filter";
import { FieldType, IFilter } from "../../../components/Filter/types";
import {
  Filter,
  FilterChips,
  FilterTab,
  FilterTabs
} from "../../../components/TableFilter";
import i18n from "../../../i18n";
import { StockAvailability } from "../../../types/globalTypes";

export type ProductListFilterTabs =
  | "all"
  | "available"
  | "outOfStock"
  | "custom";

interface ProductListFilterProps {
  currencySymbol: string;
  currentTab: ProductListFilterTabs;
  filtersList: Filter[];
  onAllProducts: () => void;
  onAvailable: () => void;
  onOfStock: () => void;
  onCustomFilter: () => void;
  onSearchChange: (value: string) => void;
  onFilterAdd: (filter: FilterContentSubmitData) => void;
}

export enum ProductFilterKeys {
  published,
  price,
  priceEqual,
  priceRange,
  stock
}
const filterMenu: IFilter = [
  {
    children: [],
    data: {
      fieldLabel: i18n.t("Status"),
      options: [
        {
          label: i18n.t("Published"),
          value: true
        },
        {
          label: i18n.t("Hidden"),
          value: false
        }
      ],
      type: FieldType.select
    },
    label: i18n.t("Published"),
    value: ProductFilterKeys.published.toString()
  },
  {
    children: [],
    data: {
      fieldLabel: i18n.t("Stock quantity"),
      options: [
        {
          label: i18n.t("Available"),
          value: StockAvailability.IN_STOCK
        },
        {
          label: i18n.t("Out Of Stock"),
          value: StockAvailability.OUT_OF_STOCK
        }
      ],
      type: FieldType.select
    },
    label: i18n.t("Stock"),
    value: ProductFilterKeys.stock.toString()
  },
  {
    children: [
      {
        children: [],
        data: {
          fieldLabel: null,
          type: FieldType.price
        },
        label: i18n.t("Specific Price"),
        value: ProductFilterKeys.priceEqual.toString()
      },
      {
        children: [],
        data: {
          fieldLabel: i18n.t("Range"),
          type: FieldType.rangePrice
        },
        label: i18n.t("Range"),
        value: ProductFilterKeys.priceRange.toString()
      }
    ],
    data: {
      fieldLabel: i18n.t("Price"),
      type: FieldType.range
    },
    label: i18n.t("Price"),
    value: ProductFilterKeys.price.toString()
  }
];

const ProductListFilter: React.StatelessComponent<ProductListFilterProps> = ({
  currencySymbol,
  filtersList,
  currentTab,
  onAllProducts,
  onAvailable,
  onOfStock,
  onCustomFilter,
  onSearchChange,
  onFilterAdd
}) => {
  const [search, setSearch] = React.useState("");

  return (
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
      <Debounce debounceFn={onSearchChange}>
        {debounceSearchChange => {
          const handleSearchChange = (event: React.ChangeEvent<any>) => {
            const value = event.target.value;
            setSearch(value);
            debounceSearchChange(value);
          };

          return (
            <FilterChips
              currencySymbol={currencySymbol}
              menu={filterMenu}
              filtersList={filtersList}
              filterLabel={i18n.t("Select all products where:")}
              placeholder={i18n.t("Search Products...")}
              search={search}
              onSearchChange={handleSearchChange}
              onFilterAdd={onFilterAdd}
            />
          );
        }}
      </Debounce>
    </>
  );
};
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
