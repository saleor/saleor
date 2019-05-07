import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedSearchProductsQuery } from "./query";
import {
  SearchProducts,
  SearchProductsVariables
} from "./types/SearchProducts";

interface SearchProductsProviderProps {
  children: ((
    search: (query: string) => void,
    searchOpts: QueryResult<SearchProducts, SearchProductsVariables>
  ) => React.ReactElement<any>);
}
interface SearchProductsProviderState {
  query: string;
}

export class SearchProductsProvider extends React.Component<
  SearchProductsProviderProps,
  SearchProductsProviderState
> {
  state: SearchProductsProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    return (
      <TypedSearchProductsQuery variables={{ query: this.state.query }}>
        {searchOpts => children(this.search, searchOpts)}
      </TypedSearchProductsQuery>
    );
  }
}
