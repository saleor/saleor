import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CategoryCreatePage from "../components/CategoryCreatePage";
import { TypedCategoryCreateMutation } from "../mutations";
import { CategoryCreate } from "../types/CategoryCreate";
import { categoryUrl } from "../urls";

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
              navigate(
                categoryUrl(encodeURIComponent(data.categoryCreate.category.id))
              );
            }
          };
          return (
            <TypedCategoryCreateMutation onCompleted={handleSuccess}>
              {(mutate, { data, loading }) => (
                <>
                  <WindowTitle title={i18n.t("Create category")} />
                  <CategoryCreatePage
                    errors={maybe(() => data.categoryCreate.errors, [])}
                    disabled={loading}
                    onBack={() =>
                      navigate(categoryUrl(encodeURIComponent(parentId)))
                    }
                    onSubmit={formData =>
                      mutate({
                        variables: {
                          input: {
                            description: formData.description,
                            name: formData.name,
                            seo: {
                              description: formData.seoDescription,
                              title: formData.seoTitle
                            }
                          },
                          parent: parentId
                        }
                      })
                    }
                  />
                </>
              )}
            </TypedCategoryCreateMutation>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
export default CategoryCreateView;
