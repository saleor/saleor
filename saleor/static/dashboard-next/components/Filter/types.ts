import { IMenu, IMenuItem } from "../../utils/menu";

export enum FieldType {
  date,
  number,
  range,
  rangeDate,
  rangePrice,
  select,
  text
}

export interface FilterData {
  type: FieldType;
}

export type IFilterItem = IMenuItem<FilterData>;

export type IFilter = IMenu<FilterData>;
