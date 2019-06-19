import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";
import { PAGINATE_BY } from "../../../config";
import useBulkActions from "../../../hooks/useBulkActions";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import AttributeBulkDeleteDialog from "../../components/AttributeBulkDeleteDialog";
import AttributeListPage from "../../components/AttributeListPage";
import { AttributeBulkDeleteMutation } from "../../mutations";
import { AttributeListQuery } from "../../queries";
import { AttributeBulkDelete } from "../../types/AttributeBulkDelete";
import {
  attributeAddUrl,
  attributeListUrl,
  AttributeListUrlDialog,
  AttributeListUrlQueryParams,
  attributeUrl
} from "../../urls";

interface AttributeListProps {
  params: AttributeListUrlQueryParams;
}

const AttributeList: React.FC<AttributeListProps> = ({ params }) => {
  const navigate = useNavigator();
  const paginate = usePaginator();
  const notify = useNotifier();
  const { isSelected, listElements, reset, toggle, toggleAll } = useBulkActions(
    params.ids
  );

  const closeModal = () =>
    navigate(
      attributeListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const openModal = (action: AttributeListUrlDialog, ids?: string[]) =>
    navigate(
      attributeListUrl({
        ...params,
        action,
        ids
      })
    );

  const paginationState = createPaginationState(PAGINATE_BY, params);
  const queryVariables = React.useMemo(() => paginationState, [params]);

  return (
    <AttributeListQuery variables={queryVariables}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.attributes.pageInfo),
          paginationState,
          params
        );

        const handleBulkDelete = (data: AttributeBulkDelete) => {
          if (data.attributeBulkDelete.errors.length === 0) {
            closeModal();
            notify({
              text: i18n.t("Attributes removed")
            });
            reset();
            refetch();
          }
        };

        return (
          <AttributeBulkDeleteMutation onCompleted={handleBulkDelete}>
            {(attributeBulkDelete, attributeBulkDeleteOpts) => {
              const bulkDeleteMutationState = getMutationState(
                attributeBulkDeleteOpts.called,
                attributeBulkDeleteOpts.loading,
                maybe(
                  () => attributeBulkDeleteOpts.data.attributeBulkDelete.errors
                )
              );

              return (
                <>
                  <AttributeListPage
                    attributes={maybe(() =>
                      data.attributes.edges.map(edge => edge.node)
                    )}
                    disabled={loading || attributeBulkDeleteOpts.loading}
                    isChecked={isSelected}
                    onAdd={() => navigate(attributeAddUrl())}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(attributeUrl(id))}
                    pageInfo={pageInfo}
                    selected={listElements.length}
                    toggle={toggle}
                    toggleAll={toggleAll}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() => openModal("remove", listElements)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  />
                  <AttributeBulkDeleteDialog
                    confirmButtonState={bulkDeleteMutationState}
                    open={params.action === "remove"}
                    onConfirm={() =>
                      attributeBulkDelete({ variables: { ids: params.ids } })
                    }
                    onClose={closeModal}
                    quantity={maybe(() => params.ids.length.toString(), "...")}
                  />
                </>
              );
            }}
          </AttributeBulkDeleteMutation>
        );
      }}
    </AttributeListQuery>
  );
};
AttributeList.displayName = "AttributeList";

export default AttributeList;
