import "./scss/index.scss";

import { stringify as stringifyQs } from "query-string";
import * as React from "react";
import { RouteComponentProps } from "react-router";

import {
  DebounceChange,
  Loader,
  OfflinePlaceholder,
  ProductsFeatured,
  ProductsList
} from "../../components";
import { Error } from "../../components/Error";
import NetworkStatus from "../../components/NetworkStatus";
import {
  AttributeList,
  Filters,
  ProductFilters
} from "../../components/ProductFilters";
import { PRODUCTS_PER_PAGE } from "../../core/config";
import {
  convertSortByFromString,
  convertToAttributeScalar,
  getAttributesFromQs,
  maybe,
  parseQueryString,
  updateQueryString
} from "../../core/utils";
import { TypedSearchProductsQuery } from "./queries";
import SearchPage from "./SearchPage";

type SearchViewProps = RouteComponentProps<{}>;

const notFound = (phrase: string) => (
  <>
    <p className="u-lead u-lead--bold u-uppercase">
      Sorry, but we couldn’t match any search results for: “{phrase}”
    </p>
    <p>
      Don’t give up - check the spelling, think of something less specific and
      then use the search bar above.
    </p>
  </>
);

export const SearchView: React.FC<SearchViewProps> = ({
  history,
  location,
}) => {
  const querystring = parseQueryString(location);
  const updateQs = updateQueryString(location, history);
  const attributes: AttributeList = getAttributesFromQs(querystring);
  const filters: Filters = {
    attributes,
    pageSize: PRODUCTS_PER_PAGE,
    priceGte: parseInt(querystring.priceGte, 0) || null,
    priceLte: parseInt(querystring.priceLte, 0) || null,
    sortBy: querystring.sortBy || null,
  };
  const variables = {
    ...filters,
    attributes: convertToAttributeScalar(filters.attributes),
    query: querystring.q,
    sortBy: convertSortByFromString(filters.sortBy),
  };
  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    querystring.q = event.target.value;
    history.replace("?" + stringifyQs(querystring));
  };

  return (
    <NetworkStatus>
      {isOnline => (
        <TypedSearchProductsQuery
          loaderFull
          variables={variables}
          errorPolicy="all"
        >
          {({ error, data, loading, loadMore }) => {
            const canDisplayFilters = maybe(
              () => !!data.attributes.edges.length
            );
            const canDisplayProducts = maybe(
              () => data.products.totalCount !== null && !!data.products.edges
            );
            const hasProducts =
              canDisplayProducts && !!data.products.totalCount;

            const handleLoadMore = () =>
              loadMore(
                (prev, next) => ({
                  ...prev,
                  products: {
                    ...prev.products,
                    edges: [...prev.products.edges, ...next.products.edges],
                    pageInfo: next.products.pageInfo,
                  },
                }),
                {
                  after: data.products.pageInfo.endCursor,
                  query: querystring.q,
                }
              );

            return (
              <DebounceChange
                debounce={handleQueryChange}
                value={querystring.q}
                time={500}
              >
                {({ change, value: query }) => {
                  if (loading) {
                    return <Loader full />;
                  }

                  if (!!error) {
                    return isOnline ? (
                      <Error error={error.message} />
                    ) : (
                      <OfflinePlaceholder />
                    );
                  }

                  return (
                    <SearchPage onQueryChange={change} query={query}>
                      {hasProducts && canDisplayFilters && (
                        <ProductFilters
                          attributes={data.attributes.edges.map(
                            edge => edge.node
                          )}
                          filters={filters}
                          onAttributeFiltersChange={updateQs}
                          onPriceChange={updateQs}
                        />
                      )}
                      {canDisplayProducts && (
                        <ProductsList
                          displayLoader={loading}
                          filters={filters}
                          hasNextPage={data.products.pageInfo.hasNextPage}
                          notFound={notFound(query)}
                          onLoadMore={handleLoadMore}
                          onOrder={updateQs}
                          products={data.products.edges.map(edge => edge.node)}
                          totalCount={data.products.totalCount}
                        />
                      )}
                      {!hasProducts && (
                        <ProductsFeatured title="You might like" />
                      )}
                    </SearchPage>
                  );
                }}
              </DebounceChange>
            );
          }}
        </TypedSearchProductsQuery>
      )}
    </NetworkStatus>
  );
};
export default SearchView;
