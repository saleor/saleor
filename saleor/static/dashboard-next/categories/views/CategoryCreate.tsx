import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import CategoryCreatePage from "../components/CategoryCreatePage";
import { TypedCategoryCreateMutation } from "../mutations";
import { CategoryCreate } from "../types/CategoryCreate";
import { categoryListUrl, categoryUrl } from "../urls";

interface CategoryCreateViewProps {
  parentId: string;
}

export const CategoryCreateView: React.StatelessComponent<
  CategoryCreateViewProps
> = ({ parentId }) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const handleSuccess = (data: CategoryCreate) => {
            if (data.categoryCreate.errors.length === 0) {
              pushMessage({ text: i18n.t("Category created") });
              navigate(categoryUrl(data.categoryCreate.category.id));
            }
          };
          return (
            <TypedCategoryCreateMutation onCompleted={handleSuccess}>
              {(createCategory, createCategoryResult) => {
                const formTransitionState = getMutationState(
                  createCategoryResult.called,
                  createCategoryResult.loading,
                  maybe(() => createCategoryResult.data.categoryCreate.errors)
                );

                return (
                  <>
                    <WindowTitle title={i18n.t("Create category")} />
                    <CategoryCreatePage
                      saveButtonBarState={formTransitionState}
                      errors={maybe(
                        () => createCategoryResult.data.categoryCreate.errors,
                        []
                      )}
                      disabled={createCategoryResult.loading}
                      onBack={() =>
                        navigate(
                          parentId ? categoryUrl(parentId) : categoryListUrl()
                        )
                      }
                      onSubmit={formData =>
                        createCategory({
                          variables: {
                            input: {
                              descriptionJson: JSON.stringify(
                                formData.description
                              ),
                              name: formData.name,
                              seo: {
                                description: formData.seoDescription,
                                title: formData.seoTitle
                              }
                            },
                            parent: parentId || null
                          }
                        })
                      }
                    />
                  </>
                );
              }}
            </TypedCategoryCreateMutation>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
export default CategoryCreateView;
