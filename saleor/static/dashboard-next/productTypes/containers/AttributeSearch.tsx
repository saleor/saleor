import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedSearchAttributeQuery } from "../queries";
import {
  SearchAttribute,
  SearchAttributeVariables
} from "../types/SearchAttribute";

interface AttributeSearchProviderProps {
  children: (
    search: (query: string) => void,
    props: QueryResult<SearchAttribute, SearchAttributeVariables>
  ) => React.ReactNode;
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
        <TypedSearchAttributeQuery variables={{ search: this.state.query }}>
          {props => children(this.search, props)}
        </TypedSearchAttributeQuery>
      );
    }
    return this.props.children;
  }
}
