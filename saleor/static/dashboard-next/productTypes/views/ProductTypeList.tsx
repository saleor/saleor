import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import { Pagination } from "../../types";
import ProductTypeListPage from "../components/ProductTypeListPage";
import { TypedProductTypeListQuery } from "../queries";
import { productTypeAddUrl, productTypeUrl } from "../urls";

export type ProductTypeListQueryParams = Pagination;

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
        <TypedProductTypeListQuery displayLoader variables={paginationState}>
          {({ data, loading }) => (
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
          )}
        </TypedProductTypeListQuery>
      );
    }}
  </Navigator>
);
ProductTypeList.displayName = "ProductTypeList";
export default ProductTypeList;
