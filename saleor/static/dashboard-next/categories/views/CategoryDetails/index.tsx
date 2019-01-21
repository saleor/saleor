import DialogContentText from "@material-ui/core/DialogContentText";
import { stringify as stringifyQs } from "qs";
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
import {
  CategoryPageTab,
  CategoryUpdatePage
} from "../../components/CategoryUpdatePage/CategoryUpdatePage";
import {
  TypedCategoryDeleteMutation,
  TypedCategoryUpdateMutation
} from "../../mutations";
import { TypedCategoryDetailsQuery } from "../../queries";
import { CategoryDelete } from "../../types/CategoryDelete";
import { categoryAddUrl, categoryListUrl, categoryUrl } from "../../urls";
import { categoryDeletePath, categoryDeleteUrl } from "./urls";

export type CategoryDetailsQueryParams = Partial<{
  activeTab: CategoryPageTab;
  after: string;
  before: string;
}>;
export interface CategoryDetailsProps {
  params: CategoryDetailsQueryParams;
  id: string;
}

export function getActiveTab(tabName: string): CategoryPageTab {
  return tabName === CategoryPageTab.products
    ? CategoryPageTab.products
    : CategoryPageTab.categories;
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
            if (data.categoryDelete.errors.length === 0) {
              pushMessage({
                text: i18n.t("Category deleted", {
                  context: "notification"
                })
              });
              navigate(categoryListUrl);
            }
          };

          const changeTab = (tabName: CategoryPageTab) =>
            navigate(
              "?" +
                stringifyQs({
                  activeTab: tabName
                })
            );

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
                        require={["category"]}
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
                                  changeTab={changeTab}
                                  currentTab={params.activeTab}
                                  category={maybe(() => data.category)}
                                  disabled={loading}
                                  errors={maybe(
                                    () =>
                                      updateResult.data.categoryUpdate.errors
                                  )}
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
                                  onImageDelete={() =>
                                    updateCategory({
                                      variables: {
                                        id,
                                        input: {
                                          backgroundImage: null
                                        }
                                      }
                                    })
                                  }
                                  onImageUpload={event =>
                                    updateCategory({
                                      variables: {
                                        id,
                                        input: {
                                          backgroundImage: event.target.files[0]
                                        }
                                      }
                                    })
                                  }
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
                                          backgroundImageAlt:
                                            formData.backgroundImageAlt,
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
