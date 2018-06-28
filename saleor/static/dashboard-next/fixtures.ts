import { PageListProps } from ".";

const pageInfo = {
  hasNextPage: true,
  hasPreviousPage: false
};
export const pageListProps: { [key: string]: PageListProps } = {
  default: {
    disabled: false,
    onAdd: () => {},
    onNextPage: () => {},
    onPreviousPage: () => {},
    onRowClick: (id: string) => () => {},
    pageInfo
  },
  loading: {
    disabled: true,
    onAdd: () => {},
    onNextPage: () => {},
    onPreviousPage: () => {},
    onRowClick: (id: string) => () => {},
    pageInfo
  }
};
