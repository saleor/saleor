import * as React from "react";
import { QueryResult } from "react-apollo";

import { LoadMore } from "../../queries";
import { TypedOrderVariantSearch } from "../queries";
import {
  OrderVariantSearch,
  OrderVariantSearchVariables
} from "../types/OrderVariantSearch";

interface OrderVariantSearchProviderProps {
  children: ((
    props: {
      variants: {
        search: (query: string) => void;
        searchOpts: QueryResult<
          OrderVariantSearch,
          OrderVariantSearchVariables
        > &
          LoadMore<OrderVariantSearch, OrderVariantSearchVariables>;
      };
    }
  ) => React.ReactElement<any>);
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
    return (
      <TypedOrderVariantSearch variables={{ search: this.state.query }}>
        {searchOpts =>
          children({ variants: { search: this.search, searchOpts } })
        }
      </TypedOrderVariantSearch>
    );
  }
}
