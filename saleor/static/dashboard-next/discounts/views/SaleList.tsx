import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import { WindowTitle } from "../../components/WindowTitle";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import useShop from "../../hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import SaleListPage from "../components/SaleListPage";
import { TypedSaleBulkDelete } from "../mutations";
import { TypedSaleList } from "../queries";
import { SaleBulkDelete } from "../types/SaleBulkDelete";
import {
  saleAddUrl,
  saleListUrl,
  SaleListUrlQueryParams,
  saleUrl
} from "../urls";

const PAGINATE_BY = 20;

interface SaleListProps {
  params: SaleListUrlQueryParams;
}

export const SaleList: React.StatelessComponent<SaleListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const shop = useShop();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const closeModal = () => navigate(saleListUrl(), true);

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedSaleList displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.sales.pageInfo),
          paginationState,
          params
        );

        const handleSaleBulkDelete = (data: SaleBulkDelete) => {
          if (data.saleBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed sales")
            });
            reset();
            closeModal();
            refetch();
          }
        };

        return (
          <TypedSaleBulkDelete onCompleted={handleSaleBulkDelete}>
            {(saleBulkDelete, saleBulkDeleteOpts) => {
              const bulkRemoveTransitionState = getMutationState(
                saleBulkDeleteOpts.called,
                saleBulkDeleteOpts.loading,
                maybe(() => saleBulkDeleteOpts.data.saleBulkDelete.errors)
              );
              const onSaleBulkDelete = () =>
                saleBulkDelete({
                  variables: {
                    ids: params.ids
                  }
                });

              return (
                <>
                  <WindowTitle title={i18n.t("Sales")} />
                  <SaleListPage
                    defaultCurrency={maybe(() => shop.defaultCurrency)}
                    sales={maybe(() => data.sales.edges.map(edge => edge.node))}
                    disabled={loading}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(saleAddUrl)}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(saleUrl(id))}
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() =>
                          navigate(
                            saleListUrl({
                              action: "remove",
                              ids: listElements
                            })
                          )
                        }
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  />
                  <ActionDialog
                    confirmButtonState={bulkRemoveTransitionState}
                    onClose={closeModal}
                    onConfirm={onSaleBulkDelete}
                    open={params.action === "remove"}
                    title={i18n.t("Remove Sales")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> sales?",
                          {
                            number: maybe(
                              () => params.ids.length.toString(),
                              "..."
                            )
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                </>
              );
            }}
          </TypedSaleBulkDelete>
        );
      }}
    </TypedSaleList>
  );
};
export default SaleList;
