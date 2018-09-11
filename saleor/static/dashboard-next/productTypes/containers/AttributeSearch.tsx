import * as React from "react";
import { QueryResult } from "react-apollo";
import {
  SearchAttributeQuery,
  SearchAttributeQueryVariables
} from "../../gql-types";
import { searchAttributeQuery, TypedSearchAttributeQuery } from "../queries";

interface AttributeSearchProviderProps {
  children:
    | ((
        search: (query: string) => void,
        props: QueryResult<SearchAttributeQuery, SearchAttributeQueryVariables>
      ) => React.ReactElement<any>)
    | React.ReactNode;
}
interface AttributeSearchProviderState {
  query: string;
}

export class AttributeSearchProvider extends React.Component<
  AttributeSearchProviderProps,
  AttributeSearchProviderState
> {
  state: AttributeSearchProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    if (typeof children === "function") {
      return (
        <TypedSearchAttributeQuery
          query={searchAttributeQuery}
          variables={{ search: this.state.query }}
          skip={!this.state.query}
        >
          {props => children(this.search, props)}
        </TypedSearchAttributeQuery>
      );
    }
    return this.props.children;
  }
}
