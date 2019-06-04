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
import { getFilterTabs } from "../../views/ProductList/filters";

interface ProductListFilterProps {
  currencySymbol: string;
  currentTab: number;
  filtersList: Filter[];
  initialSearch: string;
  onAllProducts: () => void;
  onSearchChange: (value: string) => void;
  onFilterAdd: (filter: FilterContentSubmitData) => void;
  onFilterDelete: () => void;
  onFilterSave: () => void;
  onTabChange: (tab: number) => void;
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
      additionalText: i18n.t("is set as"),
      fieldLabel: i18n.t("Status"),
      options: [
        {
          label: i18n.t("Visible"),
          value: true
        },
        {
          label: i18n.t("Hidden"),
          value: false
        }
      ],
      type: FieldType.select
    },
    label: i18n.t("Visibility"),
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
          additionalText: i18n.t("equals"),
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
  initialSearch,
  onAllProducts,
  onSearchChange,
  onFilterAdd,
  onFilterSave,
  onTabChange,
  onFilterDelete
}) => {
  const [search, setSearch] = React.useState(initialSearch);
  React.useEffect(() => setSearch(initialSearch), [currentTab, initialSearch]);

  const filterTabs = getFilterTabs();

  const isCustom = currentTab === filterTabs.length + 1;

  return (
    <>
      <FilterTabs currentTab={currentTab}>
        <FilterTab label={i18n.t("All Products")} onClick={onAllProducts} />
        {filterTabs.map((tab, tabIndex) => (
          <FilterTab
            onClick={() => onTabChange(tabIndex + 1)}
            label={tab.name}
          />
        ))}
        {isCustom && (
          <FilterTab
            onClick={() => undefined}
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
              onFilterSave={onFilterSave}
              isCustomSearch={isCustom}
              onFilterDelete={onFilterDelete}
            />
          );
        }}
      </Debounce>
    </>
  );
};
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
