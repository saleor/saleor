import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import { createPaginationState } from "../../components/Paginator";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { CategoryListPage } from "../components/CategoryListPage/CategoryListPage";
import { TypedCategoryBulkDeleteMutation } from "../mutations";
import { TypedRootCategoriesQuery } from "../queries";
import { CategoryBulkDelete } from "../types/CategoryBulkDelete";
import {
  categoryAddUrl,
  categoryListUrl,
  CategoryListUrlQueryParams,
  categoryUrl
} from "../urls";

interface CategoryListProps {
  params: CategoryListUrlQueryParams;
}

const PAGINATE_BY = 20;

export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  params
}) => {
  const navigate = useNavigator();
  const paginate = usePaginator();
  const { isSelected, listElements, toggle, reset } = useBulkActions(
    params.ids
  );

  const paginationState = createPaginationState(PAGINATE_BY, params);
  return (
    <TypedRootCategoriesQuery displayLoader variables={paginationState}>
      {({ data, loading, refetch }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.categories.pageInfo),
          paginationState,
          params
        );

        const handleCategoryBulkDelete = (data: CategoryBulkDelete) => {
          if (data.categoryBulkDelete.errors.length === 0) {
            navigate(categoryListUrl(), true);
            refetch();
            reset();
          }
        };
        return (
          <TypedCategoryBulkDeleteMutation
            onCompleted={handleCategoryBulkDelete}
          >
            {(categoryBulkDelete, categoryBulkDeleteOpts) => {
              const bulkDeleteState = getMutationState(
                categoryBulkDeleteOpts.called,
                categoryBulkDeleteOpts.loading,
                maybe(
                  () => categoryBulkDeleteOpts.data.categoryBulkDelete.errors
                )
              );

              return (
                <>
                  <CategoryListPage
                    categories={maybe(
                      () => data.categories.edges.map(edge => edge.node),
                      []
                    )}
                    onAdd={() => navigate(categoryAddUrl())}
                    onRowClick={id => () => navigate(categoryUrl(id))}
                    disabled={loading}
                    onNextPage={loadNextPage}
                    onPreviousPage={loadPreviousPage}
                    pageInfo={pageInfo}
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                    toolbar={
                      <IconButton
                        color="primary"
                        onClick={() =>
                          navigate(
                            categoryListUrl({
                              ...params,
                              action: "delete",
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
                    confirmButtonState={bulkDeleteState}
                    onClose={() =>
                      navigate(
                        categoryListUrl({
                          ...params,
                          action: undefined,
                          ids: undefined
                        })
                      )
                    }
                    onConfirm={() =>
                      categoryBulkDelete({
                        variables: {
                          ids: params.ids
                        }
                      })
                    }
                    open={params.action === "delete"}
                    title={i18n.t("Remove categories")}
                    variant="delete"
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to remove <strong>{{ number }}</strong> categories?",
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
          </TypedCategoryBulkDeleteMutation>
        );
      }}
    </TypedRootCategoriesQuery>
  );
};
export default CategoryList;
