import Button from "@material-ui/core/Button";
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
import CollectionListPage from "../components/CollectionListPage/CollectionListPage";
import { TypedCollectionBulkDelete } from "../mutations";
import { TypedCollectionListQuery } from "../queries";
import { CollectionBulkDelete } from "../types/CollectionBulkDelete";
import {
  collectionAddUrl,
  collectionListUrl,
  CollectionListUrlDialog,
  CollectionListUrlQueryParams,
  collectionUrl
} from "../urls";

interface CollectionListProps {
  params: CollectionListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const CollectionList: React.StatelessComponent<CollectionListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle } = useBulkActions();

  const closeModal = () =>
    navigate(
      collectionListUrl({
        ...params,
        action: undefined,
        ids: undefined
      }),
      true
    );

  const openModal = (action: CollectionListUrlDialog, ids: string[]) =>
    navigate(
      collectionListUrl({
        action,
        ids
      })
    );

  const paginationState = createPaginationState(PAGINATE_BY, params);
  return (
    <TypedCollectionListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.collections.pageInfo),
          paginationState,
          params
        );

        const handleCollectionBulkDelete = (data: CollectionBulkDelete) => {
          if (data.collectionBulkDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed collections")
            });
            refetch();
            reset();
            navigate(
              collectionListUrl({
                ...params,
                action: undefined,
                ids: undefined
              })
            );
          }
        };

        return (
          <TypedCollectionBulkDelete onCompleted={handleCollectionBulkDelete}>
            {(collectionBulkDelete, collectionBulkDeleteOpts) => {
              const bulkDeleteTransitionState = getMutationState(
                collectionBulkDeleteOpts.called,
                collectionBulkDeleteOpts.loading,
                maybe(
                  () =>
                    collectionBulkDeleteOpts.data.collectionBulkDelete.errors
                )
              );

              return (
                <>
                  <CollectionListPage
                    onAdd={() => navigate(collectionAddUrl)}
                    disabled={loading}
                    collections={maybe(() =>
                      data.collections.edges.map(edge => edge.node)
                    )}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    pageInfo={pageInfo}
                    onRowClick={id => () => navigate(collectionUrl(id))}
                    toolbar={
                      <>
                        <Button
                          color="primary"
                          onClick={() => openModal("unpublish", listElements)}
                        >
                          {i18n.t("Unpublish")}
                        </Button>
                        <Button
                          color="primary"
                          onClick={() => openModal("publish", listElements)}
                        >
                          {i18n.t("Publish")}
                        </Button>
                        <IconButton
                          color="primary"
                          onClick={() => openModal("remove", listElements)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </>
                    }
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                  />
                  <ActionDialog
                    open={params.action === "publish"}
                    onClose={closeModal}
                    confirmButtonState={"default"}
                    onConfirm={() => undefined}
                    variant="default"
                    title={i18n.t("Publish collections")}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to publish <strong>{{ number }}</strong> collections?",
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
                  <ActionDialog
                    open={params.action === "unpublish"}
                    onClose={closeModal}
                    confirmButtonState={"default"}
                    onConfirm={() => undefined}
                    variant="default"
                    title={i18n.t("Unpublish collections")}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to unpublish <strong>{{ number }}</strong> collections?",
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
                  <ActionDialog
                    open={params.action === "remove"}
                    onClose={closeModal}
                    confirmButtonState={bulkDeleteTransitionState}
                    onConfirm={() =>
                      collectionBulkDelete({
                        variables: {
                          ids: params.ids
                        }
                      })
                    }
                    variant="delete"
                    title={i18n.t("Remove collections")}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> collections?",
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
          </TypedCollectionBulkDelete>
        );
      }}
    </TypedCollectionListQuery>
  );
};
export default CollectionList;
