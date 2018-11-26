import { stringify as stringifyQs } from "qs";
import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import { StockAvailability } from "../../types/globalTypes";
import ProductListCard from "../components/ProductListCard";
import { getTabName } from "../misc";
import { TypedProductListQuery } from "../queries";
import { productAddUrl, productUrl } from "../urls";

export interface ProductListFilters {
  status: StockAvailability;
}
export type ProductListQueryParams = Partial<
  {
    after: string;
    before: string;
  } & ProductListFilters
>;

interface ProductListProps {
  params: ProductListQueryParams;
}

const PAGINATE_BY = 20;

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const changeFilters = (newParams: ProductListQueryParams) =>
        navigate(
          "?" +
            stringifyQs({
              ...params,
              ...newParams
            })
        );
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedProductListQuery
          displayLoader
          variables={{
            ...paginationState,
            stockAvailability: params.status
          }}
        >
          {({ data, loading, error }) => {
            if (error) {
              return <ErrorMessageCard message="Something went wrong" />;
            }

            const currentTab = getTabName(params);
            return (
              <Paginator
                pageInfo={maybe(() => data.products.pageInfo)}
                paginationState={paginationState}
                queryString={params}
              >
                {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                  <ProductListCard
                    currentTab={currentTab}
                    filtersList={[]}
                    onAdd={() => navigate(productAddUrl)}
                    disabled={loading}
                    products={
                      data &&
                      data.products !== undefined &&
                      data.products !== null
                        ? data.products.edges.map(p => p.node)
                        : undefined
                    }
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    pageInfo={pageInfo}
                    onRowClick={id => () =>
                      navigate(productUrl(encodeURIComponent(id)))}
                    onAllProducts={() =>
                      changeFilters({
                        status: undefined
                      })
                    }
                    onCustomFilter={() => undefined}
                    onAvailable={() =>
                      changeFilters({
                        status: StockAvailability.IN_STOCK
                      })
                    }
                    onOfStock={() =>
                      changeFilters({
                        status: StockAvailability.OUT_OF_STOCK
                      })
                    }
                  />
                )}
              </Paginator>
            );
          }}
        </TypedProductListQuery>
      );
    }}
  </Navigator>
);
export default ProductList;
