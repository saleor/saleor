import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import { categoryListUrl, categoryUrl, categoryAddUrl } from "../..";
import ActionDialog from "../../../components/ActionDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import i18n from "../../../i18n";
import {
  createPaginationData,
  createPaginationState,
  maybe
} from "../../../misc";
import { productUrl, productAddUrl } from "../../../products";
import { CategoryUpdatePage } from "../../components/CategoryUpdatePage/CategoryUpdatePage";
import {
  TypedCategoryDeleteMutation,
  TypedCategoryUpdateMutation
} from "../../mutations";
import { TypedCategoryDetailsQuery } from "../../queries";
import { CategoryDelete } from "../../types/CategoryDelete";
import { CategoryUpdate } from "../../types/CategoryUpdate";
import { categoryDeleteUrl } from "./urls";

export interface QueryParams {
  after?: string;
  before?: string;
}
export interface CategoryDetailsProps {
  params: QueryParams;
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
          const onCategoryUpdate = (data: CategoryUpdate) => {
            if (
              data.categoryUpdate.errors === null ||
              data.categoryUpdate.errors.length === 0
            ) {
              pushMessage({
                text: i18n.t("Category updated", {
                  context: "notification"
                })
              });
            }
          };
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
              {deleteCategory => (
                <TypedCategoryUpdateMutation onCompleted={onCategoryUpdate}>
                  {(updateCategory, updateResult) => {
                    const paginationState = createPaginationState(
                      PAGINATE_BY,
                      params
                    );
                    return (
                      <TypedCategoryDetailsQuery
                        variables={{ ...paginationState, id }}
                      >
                        {({ data, loading }) => {
                          const paginationData = createPaginationData(
                            navigate,
                            paginationState,
                            categoryUrl(id),
                            maybe(() => data.category.products.pageInfo),
                            loading
                          );
                          return (
                            <>
                              <CategoryUpdatePage
                                category={maybe(() => data.category)}
                                disabled={loading}
                                errors={maybe(
                                  () => updateResult.data.categoryUpdate.errors
                                )}
                                placeholderImage={""}
                                onAddCategory={() =>
                                  navigate(
                                    categoryAddUrl(encodeURIComponent(id))
                                  )
                                }
                                onAddProduct={() => navigate(productAddUrl)}
                                onBack={() =>
                                  navigate(
                                    categoryUrl(
                                      maybe(() =>
                                        encodeURIComponent(
                                          data.category.parent.id
                                        )
                                      )
                                    )
                                  )
                                }
                                onCategoryClick={id => () =>
                                  navigate(categoryUrl(encodeURIComponent(id)))}
                                onDelete={() =>
                                  navigate(
                                    categoryDeleteUrl(encodeURIComponent(id))
                                  )
                                }
                                onImageDelete={() => undefined}
                                onImageUpload={() => undefined}
                                onNextPage={paginationData.loadNextPage}
                                onPreviousPage={paginationData.loadPreviousPage}
                                pageInfo={paginationData.pageInfo}
                                onProductClick={id => () =>
                                  navigate(productUrl(encodeURIComponent(id)))}
                                onSubmit={formData =>
                                  updateCategory({
                                    variables: {
                                      id,
                                      input: {
                                        description: formData.description,
                                        name: formData.name,
                                        seo: {
                                          description: formData.seoDescription,
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
                                saveButtonBarState={
                                  loading ? "loading" : "default"
                                }
                                subcategories={maybe(() =>
                                  data.category.children.edges.map(
                                    edge => edge.node
                                  )
                                )}
                              />
                              <Route
                                path={categoryDeleteUrl(encodeURIComponent(id))}
                                render={({ match }) => (
                                  <ActionDialog
                                    onClose={() =>
                                      navigate(
                                        categoryUrl(encodeURIComponent(id)),
                                        true
                                      )
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
                          );
                        }}
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
