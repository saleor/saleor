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

export interface FilterChoice {
  label: string;
  value: string | boolean;
}

export interface FilterData {
  options?: FilterChoice[];
  type: FieldType;
}

export type IFilterItem = IMenuItem<FilterData>;

export type IFilter = IMenu<FilterData>;
