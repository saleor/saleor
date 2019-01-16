import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedCategorySearchQuery } from "../queries";
import {
  CategorySearch,
  CategorySearchVariables
} from "../types/CategorySearch";

interface CategorySearchProviderProps {
  children: ((
    props: {
      search: (query: string) => void;
      searchOpts: QueryResult<CategorySearch, CategorySearchVariables>;
    }
  ) => React.ReactElement<any>);
}
interface CategorySearchProviderState {
  query: string;
}

export class CategorySearchProvider extends React.Component<
  CategorySearchProviderProps,
  CategorySearchProviderState
> {
  state: CategorySearchProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    return (
      <TypedCategorySearchQuery variables={{ query: this.state.query }}>
        {searchOpts => this.props.children({ search: this.search, searchOpts })}
      </TypedCategorySearchQuery>
    );
  }
}
