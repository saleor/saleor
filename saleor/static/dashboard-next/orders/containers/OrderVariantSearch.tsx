import * as React from "react";
import { QueryResult } from "react-apollo";
import { TypedOrderVariantSearch } from "../queries";
import {
  OrderVariantSearch,
  OrderVariantSearchVariables
} from "../types/OrderVariantSearch";

interface OrderVariantSearchProviderProps {
  children:
    | ((
        props: {
          variants: {
            search: (query: string) => void;
            searchOpts: QueryResult<
              OrderVariantSearch,
              OrderVariantSearchVariables
            >;
          };
        }
      ) => React.ReactElement<any>)
    | React.ReactNode;
}
interface OrderVariantSearchProviderState {
  query: string;
}

export class OrderVariantSearchProvider extends React.Component<
  OrderVariantSearchProviderProps,
  OrderVariantSearchProviderState
> {
  state: OrderVariantSearchProviderState = { query: "" };

  search = (query: string) => this.setState({ query });

  render() {
    const { children } = this.props;
    if (typeof children === "function") {
      return (
        <TypedOrderVariantSearch
          variables={{ search: this.state.query }}
          skip={!this.state.query}
        >
          {searchOpts =>
            children({ variants: { search: this.search, searchOpts } })
          }
        </TypedOrderVariantSearch>
      );
    }
    return this.props.children;
  }
}
