import * as React from "react";

import { productAddUrl, productListUrl, productUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState } from "../../misc";
import ProductListCard from "../components/ProductListCard";
import { productListQuery, TypedProductListQuery } from "../queries";

interface ProductListProps {
  params: {
    after?: string;
    before?: string;
  };
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
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              productListUrl,
              data && data.products ? data.products.pageInfo : undefined,
              loading
            );
            return (
              <ProductListCard
                onAdd={() => navigate(productAddUrl)}
                disabled={loading}
                products={
                  data && data.products !== undefined && data.products !== null
                    ? data.products.edges.map(p => p.node)
                    : undefined
                }
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
                onRowClick={id => () =>
                  navigate(productUrl(encodeURIComponent(id)))}
              />
            );
          }}
        </TypedProductListQuery>
      );
    }}
  </Navigator>
);
export default ProductList;
