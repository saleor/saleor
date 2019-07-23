import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import React from "react";

import ActionDialog from "@saleor/components/ActionDialog";
import { configurationMenuUrl } from "@saleor/configuration";
import useBulkActions from "@saleor/hooks/useBulkActions";
import useListSettings from "@saleor/hooks/useListSettings";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import usePaginator, {
  createPaginationState
} from "@saleor/hooks/usePaginator";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import { ListViews } from "@saleor/types";
import PageListPage from "../components/PageListPage/PageListPage";
import { TypedPageBulkPublish, TypedPageBulkRemove } from "../mutations";
import { TypedPageListQuery } from "../queries";
import { PageBulkPublish } from "../types/PageBulkPublish";
import { PageBulkRemove } from "../types/PageBulkRemove";
import {
  pageCreateUrl,
  pageListUrl,
  PageListUrlDialog,
  PageListUrlQueryParams,
  pageUrl
} from "../urls";

interface PageListProps {
  params: PageListUrlQueryParams;
}

export const PageList: React.StatelessComponent<PageListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();
  const { isSelected, listElements, reset, toggle, toggleAll } = useBulkActions(
    params.ids
  );
  const { updateListSettings, settings } = useListSettings(
    ListViews.PAGES_LIST
  );
  const paginationState = createPaginationState(settings.rowNumber, params);

  return (
    <TypedPageListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.pages.pageInfo),
          paginationState,
          params
        );

        const closeModal = () =>
          navigate(
            pageListUrl({
              ...params,
              action: undefined,
              ids: undefined
            }),
            true
          );

        const openModal = (action: PageListUrlDialog, ids: string[]) =>
          navigate(
            pageListUrl({
              ...params,
              action,
              ids
            })
          );

        const handlePageBulkPublish = (data: PageBulkPublish) => {
          if (data.pageBulkPublish.errors.length === 0) {
            closeModal();
            notify({
              text: i18n.t("Published pages")
            });
            reset();
            refetch();
          }
        };

        const handlePageBulkRemove = (data: PageBulkRemove) => {
          if (data.pageBulkDelete.errors.length === 0) {
            closeModal();
            notify({
              text: i18n.t("Removed pages")
            });
            reset();
            refetch();
          }
        };

        return (
          <TypedPageBulkRemove onCompleted={handlePageBulkRemove}>
            {(bulkPageRemove, bulkPageRemoveOpts) => (
              <TypedPageBulkPublish onCompleted={handlePageBulkPublish}>
                {(bulkPagePublish, bulkPagePublishOpts) => {
                  const deleteTransitionState = getMutationState(
                    bulkPageRemoveOpts.called,
                    bulkPageRemoveOpts.loading,
                    maybe(() => bulkPageRemoveOpts.data.pageBulkDelete.errors)
                  );

                  const publishTransitionState = getMutationState(
                    bulkPagePublishOpts.called,
                    bulkPagePublishOpts.loading,
                    maybe(() => bulkPagePublishOpts.data.pageBulkPublish.errors)
                  );

                  return (
                    <>
                      <PageListPage
                        disabled={loading}
                        settings={settings}
                        pages={maybe(() =>
                          data.pages.edges.map(edge => edge.node)
                        )}
                        pageInfo={pageInfo}
                        onAdd={() => navigate(pageCreateUrl)}
                        onBack={() => navigate(configurationMenuUrl)}
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        onUpdateListSettings={updateListSettings}
                        onRowClick={id => () => navigate(pageUrl(id))}
                        toolbar={
                          <>
                            <Button
                              color="primary"
                              onClick={() =>
                                openModal("unpublish", listElements)
                              }
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
                        toggleAll={toggleAll}
                      />
                      <ActionDialog
                        open={params.action === "publish"}
                        onClose={closeModal}
                        confirmButtonState={publishTransitionState}
                        onConfirm={() =>
                          bulkPagePublish({
                            variables: {
                              ids: params.ids,
                              isPublished: true
                            }
                          })
                        }
                        title={i18n.t("Publish pages")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to publish <strong>{{ number }}</strong> pages?",
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
                        confirmButtonState={publishTransitionState}
                        onConfirm={() =>
                          bulkPagePublish({
                            variables: {
                              ids: params.ids,
                              isPublished: false
                            }
                          })
                        }
                        title={i18n.t("Unpublish pages")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to unpublish <strong>{{ number }}</strong> pages?",
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
                        confirmButtonState={deleteTransitionState}
                        onConfirm={() =>
                          bulkPageRemove({
                            variables: {
                              ids: params.ids
                            }
                          })
                        }
                        variant="delete"
                        title={i18n.t("Remove pages")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove <strong>{{ number }}</strong> pages?",
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
              </TypedPageBulkPublish>
            )}
          </TypedPageBulkRemove>
        );
      }}
    </TypedPageListQuery>
  );
};

export default PageList;
