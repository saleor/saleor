import { IMenu, IMenuItem } from "../../utils/menu";

export enum FieldType {
  date,
  hidden,
  number,
  price,
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
  additionalText?: string;
  eval?: () => string;
  fieldLabel: string;
  options?: FilterChoice[];
  type: FieldType;
}

export type IFilterItem = IMenuItem<FilterData>;

export type IFilter = IMenu<FilterData>;
