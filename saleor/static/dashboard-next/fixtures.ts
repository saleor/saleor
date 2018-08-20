import { PageListProps } from ".";

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
    onRowClick: (id: string) => undefined,
    pageInfo
  },
  loading: {
    disabled: true,
    onAdd: undefined,
    onNextPage: undefined,
    onPreviousPage: undefined,
    onRowClick: (id: string) => undefined,
    pageInfo
  }
};
