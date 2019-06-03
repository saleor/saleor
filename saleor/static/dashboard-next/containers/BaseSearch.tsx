import { DocumentNode } from "graphql";
import * as React from "react";
import { QueryResult } from "react-apollo";

import { TypedQuery } from "../queries";

const DEFAULT_SEARCH_RESULTS = 5;

interface SearchQueryVariables {
  first: number;
  query: string;
}

interface BaseSearchProps<
  TQuery,
  TQueryVariables extends SearchQueryVariables
> {
  children: (props: {
    search: (query: string) => void;
    searchOpts: QueryResult<TQuery, TQueryVariables>;
  }) => React.ReactElement<any>;
  first?: number;
  query: DocumentNode;
}
interface BaseSearchState {
  query: string;
}

class BaseSearchComponent<
  TQuery,
  TQueryVariables extends SearchQueryVariables
> extends React.Component<
  BaseSearchProps<TQuery, TQueryVariables>,
  BaseSearchState
> {
  state: BaseSearchState = {
    query: ""
  };
  queryComponent = TypedQuery<TQuery, TQueryVariables>(this.props.query);

  search = (query: string) => this.setState({ query });

  render() {
    const Query = this.queryComponent;
    const { children, first } = this.props;

    return (
      <Query
        displayLoader={true}
        variables={
          {
            first: first || DEFAULT_SEARCH_RESULTS,
            query: this.state.query
          } as any
        }
      >
        {searchOpts => children({ search: this.search, searchOpts })}
      </Query>
    );
  }
}

function BaseSearch<TQuery, TQueryVariables extends SearchQueryVariables>(
  query: DocumentNode
) {
  return (props: BaseSearchProps<TQuery, TQueryVariables>) => (
    <BaseSearchComponent {...props} query={query} />
  );
}
export default BaseSearch;
