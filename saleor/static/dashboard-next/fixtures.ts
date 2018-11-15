import { PageListProps } from "./types";

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
