import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import ProductTypeListPage from "../components/ProductTypeListPage";
import { TypedProductTypeListQuery } from "../queries";
import { productTypeAddUrl, productTypeUrl } from "../urls";

export type ProductTypeListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface ProductTypeListProps {
  params: ProductTypeListQueryParams;
}

const PAGINATE_BY = 20;

export const ProductTypeList: React.StatelessComponent<
  ProductTypeListProps
> = ({ params }) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedProductTypeListQuery variables={paginationState}>
          {({ data, loading, error }) => {
            if (error) {
              return <ErrorMessageCard message="Something went wrong" />;
            }
            return (
              <Paginator
                pageInfo={maybe(() => data.productTypes.pageInfo)}
                paginationState={paginationState}
                queryString={params}
              >
                {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                  <ProductTypeListPage
                    disabled={loading}
                    productTypes={maybe(() =>
                      data.productTypes.edges.map(edge => edge.node)
                    )}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(productTypeAddUrl)}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(productTypeUrl(id))}
                  />
                )}
              </Paginator>
            );
          }}
        </TypedProductTypeListQuery>
      );
    }}
  </Navigator>
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
