import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedSearchCategoriesQuery } from "./query";
import {
  SearchCategories,
  SearchCategoriesVariables
} from "./types/SearchCategories";

interface SearchCategoriesProviderProps {
  children: ((
    search: (query: string) => void,
    searchOpts: QueryResult<SearchCategories, SearchCategoriesVariables>
  ) => React.ReactElement<any>);
}
interface SearchCategoriesProviderState {
  query: string;
}

export class SearchCategoriesProvider extends React.Component<
  SearchCategoriesProviderProps,
  SearchCategoriesProviderState
> {
  state: SearchCategoriesProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    return (
      <TypedSearchCategoriesQuery variables={{ query: this.state.query }}>
        {searchOpts => children(this.search, searchOpts)}
      </TypedSearchCategoriesQuery>
    );
  }
}
