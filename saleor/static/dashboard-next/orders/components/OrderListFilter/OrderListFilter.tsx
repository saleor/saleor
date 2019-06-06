import * as moment from "moment-timezone";
import * as React from "react";

import { DateContext } from "@saleor/components/Date/DateContext";
import { FieldType, IFilter } from "@saleor/components/Filter";
import FilterBar from "@saleor/components/FilterBar";
import TimezoneContext from "@saleor/components/Timezone";
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
  email
}

const OrderListFilter: React.FC<OrderListFilterProps> = props => {
  const date = React.useContext(DateContext);
  const tz = React.useContext(TimezoneContext);

  const filterMenu: IFilter = [
    {
      children: [
        {
          children: [],
          data: {
            fieldLabel: null,
            type: FieldType.hidden,
            value: (tz ? moment(date).tz(tz) : moment(date))
              .subtract(7, "days")
              .toISOString()
              .split("T")[0] // Remove timezone
          },
          label: i18n.t("Last 7 Days"),
          value: OrderFilterKeys.dateLastWeek.toString()
        },
        {
          children: [],
          data: {
            fieldLabel: null,
            type: FieldType.hidden,
            value: (tz ? moment(date).tz(tz) : moment(date))
              .subtract(30, "days")
              .toISOString()
              .split("T")[0] // Remove timezone
          },
          label: i18n.t("Last 30 Days"),
          value: OrderFilterKeys.dateLastMonth.toString()
        },
        {
          children: [],
          data: {
            fieldLabel: null,
            type: FieldType.hidden,
            value: (tz ? moment(date).tz(tz) : moment(date))
              .subtract(1, "years")
              .toISOString()
              .split("T")[0] // Remove timezone
          },
          label: i18n.t("Last Year"),
          value: OrderFilterKeys.dateLastYear.toString()
        },
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

  return <FilterBar {...props} filterMenu={filterMenu} />;
};
OrderListFilter.displayName = "OrderListFilter";
export default OrderListFilter;
