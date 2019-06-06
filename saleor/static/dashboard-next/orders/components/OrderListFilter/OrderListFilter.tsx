import * as React from "react";

import { FieldType, IFilter } from "@saleor/components/Filter";
import FilterBar from "@saleor/components/FilterBar";
import i18n from "../../../i18n";
import { FilterProps } from "../../../types";
import { OrderListUrlFilters } from "../../urls";

type OrderListFilterProps = FilterProps<OrderListUrlFilters>;

export enum OrderFilterKeys {
  date,
  dateEqual,
  dateRange,
  dateLastWeek,
  dateLastMonth,
  dateLastYear,
  query
}
const filterMenu: IFilter = [
  {
    children: [
      {
        children: [],
        data: {
          additionalText: i18n.t("equals"),
          fieldLabel: null,
          type: FieldType.date
        },
        label: i18n.t("Specific Date"),
        value: OrderFilterKeys.dateEqual.toString()
      },
      {
        children: [],
        data: {
          fieldLabel: i18n.t("Range"),
          type: FieldType.rangeDate
        },
        label: i18n.t("Range"),
        value: OrderFilterKeys.dateRange.toString()
      }
    ],
    data: {
      fieldLabel: i18n.t("Date"),
      type: FieldType.select
    },
    label: i18n.t("Date"),
    value: OrderFilterKeys.date.toString()
  }
];

const OrderListFilter: React.FC<OrderListFilterProps> = props => (
  <FilterBar {...props} filterMenu={filterMenu} />
);
OrderListFilter.displayName = "OrderListFilter";
export default OrderListFilter;
