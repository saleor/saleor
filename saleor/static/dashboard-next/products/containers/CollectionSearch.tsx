import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedCollectionSearchQuery } from "../queries";
import {
  CollectionSearch,
  CollectionSearchVariables
} from "../types/CollectionSearch";

interface CollectionSearchProviderProps {
  children: ((
    props: {
      search: (query: string) => void;
      searchOpts: QueryResult<CollectionSearch, CollectionSearchVariables>;
    }
  ) => React.ReactElement<any>);
}
interface CollectionSearchProviderState {
  query: string;
}

export class CollectionSearchProvider extends React.Component<
  CollectionSearchProviderProps,
  CollectionSearchProviderState
> {
  state: CollectionSearchProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    return (
      <TypedCollectionSearchQuery variables={{ query: this.state.query }}>
        {searchOpts => this.props.children({ search: this.search, searchOpts })}
      </TypedCollectionSearchQuery>
    );
  }
}
