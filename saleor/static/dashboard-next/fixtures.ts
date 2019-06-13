import { Filter } from "./components/TableFilter";
import { FilterPageProps, ListActions, PageListProps } from "./types";

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
  toggleAll: () => undefined,
  toolbar: null
};

export const countries = [
  { code: "AF", label: "Afghanistan" },
  { code: "AX", label: "Åland Islands" },
  { code: "AL", label: "Albania" },
  { code: "DZ", label: "Algeria" },
  { code: "AS", label: "American Samoa" }
];

export const filterPageProps: FilterPageProps<{}> = {
  currencySymbol: "USD",
  currentTab: 0,
  filterTabs: [
    {
      data: {},
      name: "Tab X"
    }
  ],
  filtersList: [],
  initialSearch: "",
  onAll: () => undefined,
  onFilterAdd: () => undefined,
  onFilterDelete: () => undefined,
  onFilterSave: () => undefined,
  onSearchChange: () => undefined,
  onTabChange: () => undefined
};

export const filters: Filter[] = [
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  },
  {
    label: "Property X is ",
    onClick: () => undefined
  },
  {
    label: "Property Y is ",
    onClick: () => undefined
  },
  {
    label: "Property Z is ",
    onClick: () => undefined
  }
].map((filter, filterIndex) => ({
  ...filter,
  label: filter.label + filterIndex
}));
