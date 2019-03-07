import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { Pagination } from "../../types";
import SaleListPage from "../components/SaleListPage";
import { TypedSaleList } from "../queries";
import { saleAddUrl, saleUrl } from "../urls";

const PAGINATE_BY = 20;

export type SaleListQueryParams = Pagination;

interface SaleListProps {
  params: SaleListQueryParams;
}

export const SaleList: React.StatelessComponent<SaleListProps> = ({
  params
}) => (
  <>
    <WindowTitle title={i18n.t("Sales")} />
    <Shop>
      {shop => (
        <Navigator>
          {navigate => {
            const paginationState = createPaginationState(PAGINATE_BY, params);
            return (
              <TypedSaleList displayLoader variables={paginationState}>
                {({ data, loading }) => (
                  <Paginator
                    pageInfo={maybe(() => data.sales.pageInfo)}
                    paginationState={paginationState}
                    queryString={params}
                  >
                    {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                      <SaleListPage
                        defaultCurrency={maybe(() => shop.defaultCurrency)}
                        sales={maybe(() =>
                          data.sales.edges.map(edge => edge.node)
                        )}
                        disabled={loading}
                        pageInfo={pageInfo}
                        onAdd={() => navigate(saleAddUrl)}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        onRowClick={id => () => navigate(saleUrl(id))}
                      />
                    )}
                  </Paginator>
                )}
              </TypedSaleList>
            );
          }}
        </Navigator>
      )}
    </Shop>
  </>
);
export default SaleList;
