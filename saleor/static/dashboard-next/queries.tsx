import { DocumentNode } from "graphql";
import gql from "graphql-tag";
import * as React from "react";
import { Query, QueryResult } from "react-apollo";

import { ApolloQueryResult } from "apollo-client";
import AppProgress from "./components/AppProgress";
import ErrorPage from "./components/ErrorPage/ErrorPage";
import Messages from "./components/messages";
import Navigator from "./components/Navigator";
import i18n from "./i18n";
import { RequireAtLeastOne } from "./misc";

export interface LoadMore<TData, TVariables> {
  loadMore: (
    mergeFunc: (prev: TData, next: TData) => TData,
    extraVariables: RequireAtLeastOne<TVariables>
  ) => Promise<ApolloQueryResult<TData>>;
}

interface TypedQueryInnerProps<TData, TVariables> {
  children: (
    result: QueryResult<TData, TVariables> & LoadMore<TData, TVariables>
  ) => React.ReactNode;
  displayLoader?: boolean;
  skip?: boolean;
  variables?: TVariables;
  require?: Array<keyof TData>;
}

interface QueryProgressProps {
  loading: boolean;
  onLoading: () => void;
  onCompleted: () => void;
}

class QueryProgress extends React.Component<QueryProgressProps, {}> {
  componentDidMount() {
    const { loading, onLoading } = this.props;
    if (loading) {
      onLoading();
    }
  }

  componentDidUpdate(prevProps) {
    const { loading, onLoading, onCompleted } = this.props;
    if (prevProps.loading !== loading) {
      if (loading) {
        onLoading();
      } else {
        onCompleted();
      }
    }
  }

  render() {
    return this.props.children;
  }
}

export function TypedQuery<TData, TVariables>(query: DocumentNode) {
  class StrictTypedQuery extends Query<TData, TVariables> {}
  return (props: TypedQueryInnerProps<TData, TVariables>) => (
    <AppProgress>
      {({ funcs: changeProgressState }) => (
        <Navigator>
          {navigate => (
            <Messages>
              {pushMessage => {
                // Obviously, this is workaround to the problem described here:
                // https://github.com/DefinitelyTyped/DefinitelyTyped/issues/32588
                const {
                  children,
                  displayLoader,
                  skip,
                  variables,
                  require
                } = props as JSX.LibraryManagedAttributes<
                  typeof StrictTypedQuery,
                  typeof props
                >;
                return (
                  <StrictTypedQuery
                    fetchPolicy="cache-and-network"
                    query={query}
                    variables={variables}
                    skip={skip}
                    context={{ useBatching: true }}
                  >
                    {queryData => {
                      if (queryData.error) {
                        const msg = i18n.t(
                          "Something went wrong: {{ message }}",
                          {
                            message: queryData.error.message
                          }
                        );
                        pushMessage({ text: msg });
                      }

                      const loadMore = (
                        mergeFunc: (
                          previousResults: TData,
                          fetchMoreResult: TData
                        ) => TData,
                        extraVariables: RequireAtLeastOne<TVariables>
                      ) =>
                        queryData.fetchMore({
                          query,
                          updateQuery: (
                            previousResults,
                            { fetchMoreResult }
                          ) => {
                            if (!fetchMoreResult) {
                              return previousResults;
                            }
                            return mergeFunc(previousResults, fetchMoreResult);
                          },
                          variables: { ...variables, ...extraVariables }
                        });

                      let childrenOrNotFound = children({
                        ...queryData,
                        loadMore
                      });
                      if (
                        !queryData.loading &&
                        require &&
                        queryData.data &&
                        !require.reduce(
                          (acc, key) => acc && queryData.data[key] !== null,
                          true
                        )
                      ) {
                        childrenOrNotFound = (
                          <ErrorPage onBack={() => navigate("/")} />
                        );
                      }

                      if (displayLoader) {
                        return (
                          <QueryProgress
                            loading={queryData.loading}
                            onCompleted={changeProgressState.disable}
                            onLoading={changeProgressState.enable}
                          >
                            {childrenOrNotFound}
                          </QueryProgress>
                        );
                      }

                      return childrenOrNotFound;
                    }}
                  </StrictTypedQuery>
                );
              }}
            </Messages>
          )}
        </Navigator>
      )}
    </AppProgress>
  );
}

export const pageInfoFragment = gql`
  fragment PageInfoFragment on PageInfo {
    endCursor
    hasNextPage
    hasPreviousPage
    startCursor
  }
`;
