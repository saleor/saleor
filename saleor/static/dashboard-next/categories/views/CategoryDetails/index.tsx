import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../../components/ActionDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import {
  createPaginationState,
  Paginator
} from "../../../components/Paginator";
import { WindowTitle } from "../../../components/WindowTitle";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { productAddUrl, productUrl } from "../../../products/urls";
import { CategoryUpdatePage } from "../../components/CategoryUpdatePage/CategoryUpdatePage";
import {
  TypedCategoryDeleteMutation,
  TypedCategoryUpdateMutation
} from "../../mutations";
import { TypedCategoryDetailsQuery } from "../../queries";
import { CategoryDelete } from "../../types/CategoryDelete";
import { categoryAddUrl, categoryListUrl, categoryUrl } from "../../urls";
import { categoryDeletePath, categoryDeleteUrl } from "./urls";

export type CategoryDetailsQueryParams = Partial<{
  after: string;
  before: string;
}>;
export interface CategoryDetailsProps {
  params: CategoryDetailsQueryParams;
  id: string;
}

const PAGINATE_BY = 20;

export const CategoryDetails: React.StatelessComponent<
  CategoryDetailsProps
> = ({ id, params }) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const onCategoryDelete = (data: CategoryDelete) => {
            if (
              data.categoryDelete.errors === null ||
              data.categoryDelete.errors.length === 0
            ) {
              pushMessage({
                text: i18n.t("Category deleted", {
                  context: "notification"
                })
              });
              navigate(categoryListUrl);
            }
          };

          return (
            <TypedCategoryDeleteMutation onCompleted={onCategoryDelete}>
              {(deleteCategory, deleteResult) => (
                <TypedCategoryUpdateMutation>
                  {(updateCategory, updateResult) => {
                    const paginationState = createPaginationState(
                      PAGINATE_BY,
                      params
                    );
                    const formTransitionState = getMutationState(
                      updateResult.called,
                      updateResult.loading,
                      maybe(() => updateResult.data.categoryUpdate.errors)
                    );
                    const removeDialogTransitionState = getMutationState(
                      deleteResult.called,
                      deleteResult.loading,
                      maybe(() => deleteResult.data.categoryDelete.errors)
                    );
                    return (
                      <TypedCategoryDetailsQuery
                        displayLoader
                        variables={{ ...paginationState, id }}
                      >
                        {({ data, loading }) => (
                          <>
                            <WindowTitle
                              title={maybe(() => data.category.name)}
                            />
                            <Paginator
                              pageInfo={maybe(
                                () => data.category.products.pageInfo
                              )}
                              paginationState={paginationState}
                              queryString={params}
                            >
                              {({
                                loadNextPage,
                                loadPreviousPage,
                                pageInfo
                              }) => (
                                <CategoryUpdatePage
                                  category={maybe(() => data.category)}
                                  disabled={loading}
                                  errors={maybe(
                                    () =>
                                      updateResult.data.categoryUpdate.errors
                                  )}
                                  placeholderImage={""}
                                  onAddCategory={() =>
                                    navigate(categoryAddUrl(id))
                                  }
                                  onAddProduct={() => navigate(productAddUrl)}
                                  onBack={() =>
                                    navigate(
                                      maybe(
                                        () =>
                                          categoryUrl(data.category.parent.id),
                                        categoryListUrl
                                      )
                                    )
                                  }
                                  onCategoryClick={id => () =>
                                    navigate(categoryUrl(id))}
                                  onDelete={() =>
                                    navigate(categoryDeleteUrl(id))
                                  }
                                  onImageDelete={() => undefined}
                                  onImageUpload={() => undefined}
                                  onNextPage={loadNextPage}
                                  onPreviousPage={loadPreviousPage}
                                  pageInfo={pageInfo}
                                  onProductClick={id => () =>
                                    navigate(productUrl(id))}
                                  onSubmit={formData =>
                                    updateCategory({
                                      variables: {
                                        id,
                                        input: {
                                          description: formData.description,
                                          name: formData.name,
                                          seo: {
                                            description:
                                              formData.seoDescription,
                                            title: formData.seoTitle
                                          }
                                        }
                                      }
                                    })
                                  }
                                  products={maybe(() =>
                                    data.category.products.edges.map(
                                      edge => edge.node
                                    )
                                  )}
                                  saveButtonBarState={formTransitionState}
                                  subcategories={maybe(() =>
                                    data.category.children.edges.map(
                                      edge => edge.node
                                    )
                                  )}
                                />
                              )}
                            </Paginator>
                            <Route
                              path={categoryDeletePath(":id")}
                              render={({ match }) => (
                                <ActionDialog
                                  confirmButtonState={
                                    removeDialogTransitionState
                                  }
                                  onClose={() =>
                                    navigate(categoryUrl(id), true)
                                  }
                                  onConfirm={() =>
                                    deleteCategory({ variables: { id } })
                                  }
                                  open={!!match}
                                  title={i18n.t("Delete category", {
                                    context: "modal title"
                                  })}
                                  variant="delete"
                                >
                                  <DialogContentText
                                    dangerouslySetInnerHTML={{
                                      __html: i18n.t(
                                        "Are you sure you want to remove <strong>{{ categoryName }}</strong>?",
                                        {
                                          categoryName: maybe(
                                            () => data.category.name
                                          ),
                                          context: "modal message"
                                        }
                                      )
                                    }}
                                  />
                                </ActionDialog>
                              )}
                            />
                          </>
                        )}
                      </TypedCategoryDetailsQuery>
                    );
                  }}
                </TypedCategoryUpdateMutation>
              )}
            </TypedCategoryDeleteMutation>
          );
        }}
      </Messages>
    )}
  </Navigator>
);
export default CategoryDetails;
