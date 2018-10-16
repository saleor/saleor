import * as React from "react";

import { categoryUrl } from "../";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CategoryCreatePage from "../components/CategoryCreatePage";
import { TypedCategoryCreateMutation } from "../mutations";
import { CategoryCreate } from "../types/CategoryCreate";

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
                          parent: parentId,
                          seo: {
                            description: formData.seoDescription,
                            title: formData.seoTitle
                          }
                        }
                      }
                    })
                  }
                />
              )}
            </TypedCategoryCreateMutation>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
export default CategoryCreateView;
