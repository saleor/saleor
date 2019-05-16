export enum FieldType {
  date,
  number,
  range,
  select,
  text
}

export interface FilterData {
  label: React.ReactNode;
  value: string;
  type: FieldType;
}

export interface FilterChildren {
  children?: Filter[];
}
export type Filter = FilterData & FilterChildren;

function validateOptions();
