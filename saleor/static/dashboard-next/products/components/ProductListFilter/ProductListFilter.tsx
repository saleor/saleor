import React from "react";

import { FieldType, IFilter } from "@saleor/components/Filter";
import FilterBar from "@saleor/components/FilterBar";
import i18n from "@saleor/i18n";
import { FilterProps } from "@saleor/types";
import { StockAvailability } from "@saleor/types/globalTypes";
import { ProductListUrlFilters } from "../../urls";

type ProductListFilterProps = FilterProps<ProductListUrlFilters>;

export enum ProductFilterKeys {
  published,
  price,
  priceEqual,
  priceRange,
  stock,
  query
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

const ProductListFilter: React.FC<ProductListFilterProps> = props => (
  <FilterBar {...props} filterMenu={filterMenu} />
);
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
