import { ApolloError } from "apollo-client";
import { MutationFn } from "react-apollo";

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
export interface PageListProps extends ListProps {
  onAdd: () => void;
}

// These interfaces are used in atomic mutation providers, which then are
// combined into one compound mutation provider
export interface PartialMutationProviderProps<T extends {} = {}> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApolloError) => void;
}
export interface PartialMutationProviderOutput<
  TData extends {} = {},
  TVariables extends {} = {}
> {
  called?: boolean;
  data: TData;
  loading: boolean;
  mutate: (variables: TVariables) => void;
}
export type PartialMutationProviderRenderProps<
  TData extends {} = {},
  TVariables extends {} = {}
> = (
  props: {
    called?: boolean;
    data: TData;
    loading: boolean;
    error?: ApolloError;
    mutate: MutationFn<TData, TVariables>;
  }
) => React.ReactElement<any>;

export interface MutationProviderProps {
  onError?: (error: ApolloError) => void;
}
export type MutationProviderRenderProps<T> = (
  props: T & { errors?: UserError[] }
) => React.ReactElement<any>;
