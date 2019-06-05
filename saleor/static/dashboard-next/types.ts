import { MutationResult } from "react-apollo";

import { Filter } from "./components/TableFilter";

export interface UserError {
  field: string;
  message: string;
}

export interface ListProps {
  disabled: boolean;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onNextPage: () => void;
  onPreviousPage: () => void;
  onRowClick: (id: string) => () => void;
}
export interface ListActionsWithoutToolbar {
  toggle: (id: string) => void;
  toggleAll: (items: React.ReactNodeArray, selected: number) => void;
  isChecked: (id: string) => boolean;
  selected: number;
}
export type TabListActions<
  TToolbars extends string
> = ListActionsWithoutToolbar &
  Record<TToolbars, React.ReactNode | React.ReactNodeArray>;
export interface ListActions extends ListActionsWithoutToolbar {
  toolbar: React.ReactNode | React.ReactNodeArray;
}
export interface PageListProps extends ListProps {
  onAdd: () => void;
}
export interface FilterProps<TFilterContentSubmitData> {
  currentTab: number;
  filtersList: Filter[];
  initialSearch: string;
  onAllProducts: () => void;
  onSearchChange: (value: string) => void;
  onFilterAdd: (filter: TFilterContentSubmitData) => void;
  onFilterDelete: () => void;
  onFilterSave: () => void;
  onTabChange: (tab: number) => void;
}

export interface PartialMutationProviderOutput<
  TData extends {} = {},
  TVariables extends {} = {}
> {
  opts: MutationResult<TData>;
  mutate: (variables: TVariables) => void;
}

export interface Node {
  id: string;
}

export type FormErrors<TKeys extends string> = Partial<Record<TKeys, string>>;

export type Pagination = Partial<{
  after: string;
  before: string;
}>;

export type Dialog<TDialog extends string> = Partial<{
  action: TDialog;
}>;
export type ActiveTab<TTab extends string = string> = Partial<{
  activeTab: TTab;
}>;
export type Filters<TFilters extends string> = Partial<
  Record<TFilters, string>
>;
export type SingleAction = Partial<{
  id: string;
}>;
export type BulkAction = Partial<{
  ids: string[];
}>;
