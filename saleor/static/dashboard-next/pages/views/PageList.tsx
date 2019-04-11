import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import { configurationMenuUrl } from "../../configuration";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import PageListPage from "../components/PageListPage/PageListPage";
import { TypedPageBulkRemove } from "../mutations";
import { TypedPageListQuery } from "../queries";
import { PageBulkRemove } from "../types/PageBulkRemove";
import {
  pageCreateUrl,
  pageListUrl,
  PageListUrlQueryParams,
  pageUrl
} from "../urls";

interface PageListProps {
  params: PageListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const PageList: React.StatelessComponent<PageListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TypedPageListQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.pages.pageInfo),
          paginationState,
          params
        );

        const handlePageBulkRemove = (data: PageBulkRemove) => {
          if (data.pageBulkDelete.errors.length === 0) {
            navigate(
              pageListUrl({
                ...params,
                action: undefined
              })
            );
            notify({
              text: i18n.t("Removed pages")
            });
            refetch();
          }
        };

        return (
          <TypedPageBulkRemove onCompleted={handlePageBulkRemove}>
            {(bulkPageRemove, bulkPageRemoveOpts) => {
              const deleteTransitionState = getMutationState(
                bulkPageRemoveOpts.called,
                bulkPageRemoveOpts.loading,
                maybe(() => bulkPageRemoveOpts.data.pageBulkDelete.errors)
              );

              return (
                <>
                  <PageListPage
                    disabled={loading}
                    pages={maybe(() => data.pages.edges.map(edge => edge.node))}
                    pageInfo={pageInfo}
                    onAdd={() => navigate(pageCreateUrl)}
                    onBack={() => navigate(configurationMenuUrl)}
                    onBulkDelete={ids =>
                      navigate(
                        pageListUrl({
                          ...params,
                          action: "remove",
                          ids
                        })
                      )
                    }
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    onRowClick={id => () => navigate(pageUrl(id))}
                  />
                  <ActionDialog
                    open={params.action === "remove"}
                    onClose={() =>
                      navigate(
                        pageListUrl({
                          ...params,
                          action: undefined,
                          ids: undefined
                        }),
                        true
                      )
                    }
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
          </TypedPageBulkRemove>
        );
      }}
    </TypedPageListQuery>
  );
};

export default PageList;
