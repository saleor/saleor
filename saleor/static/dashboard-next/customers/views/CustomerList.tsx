import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import CustomerListPage from "../components/CustomerListPage";
import { TypedBulkRemoveCustomers } from "../mutations";
import { TypedCustomerListQuery } from "../queries";
import { BulkRemoveCustomers } from "../types/BulkRemoveCustomers";
import {
  customerAddUrl,
  customerListUrl,
  CustomerListUrlQueryParams,
  customerUrl
} from "../urls";

const PAGINATE_BY = 20;

interface CustomerListProps {
  params: CustomerListUrlQueryParams;
}

export const CustomerList: React.StatelessComponent<CustomerListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  const closeModal = () =>
    navigate(
      customerListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedCustomerListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.customers.pageInfo),
          paginationState,
          params
        );

        const handleBulkCustomerDelete = (data: BulkRemoveCustomers) => {
          if (data.customerBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Customers removed")
            });
            reset();
            refetch();
            closeModal();
          }
        };

        return (
          <TypedBulkRemoveCustomers onCompleted={handleBulkCustomerDelete}>
            {(bulkRemoveCustomers, bulkRemoveCustomersOpts) => {
              const removeTransitionState = getMutationState(
                bulkRemoveCustomersOpts.called,
                bulkRemoveCustomersOpts.loading,
                maybe(
                  () => bulkRemoveCustomersOpts.data.customerBulkDelete.errors
                )
              );

              return (
                <>
                  <CustomerListPage
                    customers={maybe(() =>
                      data.customers.edges.map(edge => edge.node)
                    )}
                    disabled={loading}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(customerAddUrl)}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(customerUrl(id))}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() =>
                          navigate(
                            customerListUrl({
                              action: "remove",
                              ids: listElements
                            })
                          )
                        }
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                  />
                  <ActionDialog
                    open={params.action === "remove"}
                    onClose={closeModal}
                    confirmButtonState={removeTransitionState}
                    onConfirm={() =>
                      bulkRemoveCustomers({
                        variables: {
                          ids: params.ids
                        }
                      })
                    }
                    variant="delete"
                    title={i18n.t("Remove customers")}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> customers?",
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
          </TypedBulkRemoveCustomers>
        );
      }}
    </TypedCustomerListQuery>
  );
};
export default CustomerList;
