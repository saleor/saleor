import * as React from "react";

import { productAddUrl, productUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import ProductListCard from "../components/ProductListCard";
import { productListQuery, TypedProductListQuery } from "../queries";

export type ProductListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface ProductListProps {
  params: ProductListQueryParams;
}

const PAGINATE_BY = 20;

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedProductListQuery
          query={productListQuery}
          variables={paginationState}
          fetchPolicy="network-only"
        >
          {({ data, loading, error }) => {
            if (error) {
              return <ErrorMessageCard message="Something went wrong" />;
            }
            return (
              <Paginator
                pageInfo={maybe(() => data.products.pageInfo)}
                paginationState={paginationState}
                queryString={params}
              >
                {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                  <ProductListCard
                    currentTab={0}
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
                    onAllProducts={() => undefined}
                    onToFulfill={() => undefined}
                    onToCapture={() => undefined}
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
