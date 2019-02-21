import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { Pagination } from "../../types";
import VoucherListPage from "../components/VoucherListPage";
import { TypedVoucherList } from "../queries";
import { voucherAddUrl, voucherUrl } from "../urls";

const PAGINATE_BY = 20;

export type VoucherListQueryParams = Pagination;

interface VoucherListProps {
  params: VoucherListQueryParams;
}

export const VoucherList: React.StatelessComponent<VoucherListProps> = ({
  params
}) => (
  <>
    <WindowTitle title={i18n.t("Vouchers")} />
    <Shop>
      {shop => (
        <Navigator>
          {navigate => {
            const paginationState = createPaginationState(PAGINATE_BY, params);
            return (
              <TypedVoucherList displayLoader variables={paginationState}>
                {({ data, loading }) => (
                  <Paginator
                    pageInfo={maybe(() => data.vouchers.pageInfo)}
                    paginationState={paginationState}
                    queryString={params}
                  >
                    {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                      <VoucherListPage
                        defaultCurrency={maybe(() => shop.defaultCurrency)}
                        vouchers={maybe(() =>
                          data.vouchers.edges.map(edge => edge.node)
                        )}
                        disabled={loading}
                        pageInfo={pageInfo}
                        onAdd={() => navigate(voucherAddUrl)}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        onRowClick={id => () => navigate(voucherUrl(id))}
                      />
                    )}
                  </Paginator>
                )}
              </TypedVoucherList>
            );
          }}
        </Navigator>
      )}
    </Shop>
  </>
);
export default VoucherList;
