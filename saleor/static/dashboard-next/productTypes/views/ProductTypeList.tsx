import * as React from "react";

import { productTypeListUrl } from "../";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState } from "../../misc";
import ProductTypeListPage from "../components/ProductTypeListPage";
import { productTypeListQuery, TypedProductTypeListQuery } from "../queries";

interface ProductTypeListProps {
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 3;

export const ProductTypeList: React.StatelessComponent<
  ProductTypeListProps
> = ({ params }) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedProductTypeListQuery
          query={productTypeListQuery}
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
              productTypeListUrl,
              data && data.productTypes
                ? data.productTypes.pageInfo
                : undefined,
              loading
            );
            return (
              <ProductTypeListPage
                disabled={loading}
                productTypes={
                  data && data.productTypes
                    ? data.productTypes.edges.map(edge => edge.node)
                    : undefined
                }
                pageInfo={pageInfo}
                onAdd={() => undefined}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                onRowClick={id => () => undefined}
              />
            );
          }}
        </TypedProductTypeListQuery>
      );
    }}
  </Navigator>
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
