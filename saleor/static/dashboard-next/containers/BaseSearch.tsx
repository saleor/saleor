import { DocumentNode } from "graphql";
import React from "react";

import Debounce from "../components/Debounce";
import { TypedQuery, TypedQueryResult } from "../queries";

export interface SearchQueryVariables {
  after?: string;
  first: number;
  query: string;
}

function BaseSearch<TQuery, TQueryVariables extends SearchQueryVariables>(
  query: DocumentNode
) {
  const Query = TypedQuery<TQuery, TQueryVariables>(query);
  interface BaseSearchProps {
    children: (props: {
      search: (query: string) => void;
      result: TypedQueryResult<TQuery, TQueryVariables>;
    }) => React.ReactElement<any>;
    variables: TQueryVariables;
  }
  interface BaseSearchState {
    query: string;
  }

  class BaseSearchComponent extends React.Component<
    BaseSearchProps,
    BaseSearchState
  > {
    state: BaseSearchState = {
      query: this.props.variables.query
    };

    search = (query: string) => {
      if (query === undefined) {
        this.setState({ query: "" });
      } else {
        this.setState({ query });
      }
    };

    render() {
      const { children, variables } = this.props;

      return (
        <Debounce debounceFn={this.search} time={200}>
          {search => (
            <Query
              displayLoader={true}
              variables={{
                ...variables,
                query: this.state.query
              }}
            >
              {result => children({ search, result })}
            </Query>
          )}
        </Debounce>
      );
    }
  }
  return BaseSearchComponent;
}
export default BaseSearch;
