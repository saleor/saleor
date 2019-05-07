import { ListActions, PageListProps } from "./types";

const pageInfo = {
  hasNextPage: true,
  hasPreviousPage: false
};
export const pageListProps: { [key: string]: PageListProps } = {
  default: {
    disabled: false,
    onAdd: undefined,
    onNextPage: undefined,
    onPreviousPage: undefined,
    onRowClick: () => undefined,
    pageInfo
  },
  loading: {
    disabled: true,
    onAdd: undefined,
    onNextPage: undefined,
    onPreviousPage: undefined,
    onRowClick: () => undefined,
    pageInfo
  }
};
export const listActionsProps: ListActions = {
  isChecked: () => undefined,
  selected: 0,
  toggle: () => undefined,
  toolbar: null
};

export const countries = [
  { code: "AF", label: "Afghanistan" },
  { code: "AX", label: "Åland Islands" },
  { code: "AL", label: "Albania" },
  { code: "DZ", label: "Algeria" },
  { code: "AS", label: "American Samoa" }
];
