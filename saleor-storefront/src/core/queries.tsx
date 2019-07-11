import { ApolloQueryResult, ErrorPolicy, FetchPolicy } from "apollo-client";
import { DocumentNode } from "graphql";
import * as React from "react";
import { Query, QueryProps, QueryResult } from "react-apollo";

import { Error } from "../components/Error";
import Loader from "../components/Loader";
import { RequireAtLeastOne } from "./tsUtils";
import { maybe } from "./utils";

interface LoadMore<TData, TVariables> {
  loadMore: (
    mergeFunc: (prev: TData, next: TData) => TData,
    extraVariables: RequireAtLeastOne<TVariables>
  ) => Promise<ApolloQueryResult<TData>>;
}

interface TypedQueryInnerProps<TData, TVariables> {
  children: (
    result: QueryResult<TData, TVariables> & LoadMore<TData, TVariables>
  ) => React.ReactNode;
  displayError?: boolean;
  displayLoader?: boolean;
  fetchPolicy?: FetchPolicy;
  loaderFull?: boolean;
  renderOnError?: boolean;
  skip?: boolean;
  variables?: TVariables;
  errorPolicy?: ErrorPolicy;
  alwaysRender?: boolean;
  onCompleted?: (data: TData) => void;
}

export function TypedQuery<TData, TVariables>(query: DocumentNode) {
  return (props: TypedQueryInnerProps<TData, TVariables>) => {
    const {
      children,
      displayError = true,
      displayLoader = true,
      renderOnError = false,
      alwaysRender = false,
      fetchPolicy = "cache-and-network",
      errorPolicy,
      loaderFull,
      skip,
      variables,
      onCompleted,
    } = props as JSX.LibraryManagedAttributes<
      QueryProps<TData, TVariables>,
      TypedQueryInnerProps<TData, TVariables>
    >;
    return (
      <Query
        query={query}
        variables={variables}
        skip={skip}
        fetchPolicy={fetchPolicy}
        errorPolicy={errorPolicy}
        onCompleted={onCompleted}
      >
        {(
          queryData: QueryResult<TData, TVariables> &
            LoadMore<TData, TVariables>
        ) => {
          const { error, loading, data, fetchMore } = queryData;
          const hasData = maybe(() => !!Object.keys(data).length, false);
          const loadMore = (
            mergeFunc: (
              previousResults: TData,
              fetchMoreResult: TData
            ) => TData,
            extraVariables: RequireAtLeastOne<TVariables>
          ) =>
            fetchMore({
              query,
              updateQuery: (previousResults, { fetchMoreResult }) => {
                if (!fetchMoreResult) {
                  return previousResults;
                }
                return mergeFunc(previousResults, fetchMoreResult);
              },
              variables: { ...variables, ...extraVariables },
            });

          if (displayError && error && !hasData) {
            return <Error error={error.message} />;
          }

          if (displayLoader && loading && !hasData) {
            return <Loader full={loaderFull} />;
          }

          if (hasData || (renderOnError && error) || alwaysRender) {
            return children({ ...queryData, loadMore });
          }

          return null;
        }}
      </Query>
    );
  };
}
