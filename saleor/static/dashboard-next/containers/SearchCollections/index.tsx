import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedSearchCollectionsQuery } from "./query";
import {
  SearchCollections,
  SearchCollectionsVariables
} from "./types/SearchCollections";

interface SearchCollectionsProviderProps {
  children: ((
    search: (query: string) => void,
    searchOpts: QueryResult<SearchCollections, SearchCollectionsVariables>
  ) => React.ReactElement<any>);
}
interface SearchCollectionsProviderState {
  query: string;
}

export class SearchCollectionsProvider extends React.Component<
  SearchCollectionsProviderProps,
  SearchCollectionsProviderState
> {
  state: SearchCollectionsProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    return (
      <TypedSearchCollectionsQuery variables={{ query: this.state.query }}>
        {searchOpts => children(this.search, searchOpts)}
      </TypedSearchCollectionsQuery>
    );
  }
}
