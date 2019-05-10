import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedSearchPagesQuery } from "./query";
import { SearchPages, SearchPagesVariables } from "./types/SearchPages";

interface SearchPagesProviderProps {
  children: (props: {
    search: (query: string) => void;
    searchOpts: QueryResult<SearchPages, SearchPagesVariables>;
  }) => React.ReactElement<any>;
}
interface SearchPagesProviderState {
  query: string;
}

export class SearchPagesProvider extends React.Component<
  SearchPagesProviderProps,
  SearchPagesProviderState
> {
  state: SearchPagesProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    return (
      <TypedSearchPagesQuery variables={{ query: this.state.query }}>
        {searchOpts => children({ search: this.search, searchOpts })}
      </TypedSearchPagesQuery>
    );
  }
}
