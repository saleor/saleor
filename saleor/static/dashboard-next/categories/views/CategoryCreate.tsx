import * as React from "react";

import Messages from "../../components/messages";
import Navigator, { NavigatorLink } from "../../components/Navigator";
import { CategoryCreateMutation } from "../../gql-types";
import i18n from "../../i18n";
import CategoryEditPage from "../components/CategoryEditPage";
import { categoryShowUrl } from "../index";
import {
  TypedCategoryCreateMutation
} from "../mutations";

interface CategoryCreateFormProps {
  parentId: string;
}

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const handleSuccess = (data: CategoryCreateMutation) => {
            if (data.categoryCreate.errors.length === 0) {
              pushMessage({ text: i18n.t("Category created") });
              navigate(categoryShowUrl(data.categoryCreate.category.id));
            }
          };
          return (
            <TypedCategoryCreateMutation onCompleted={handleSuccess}>
              {(
                mutate,
                { called, data: createResult, loading: createInProgress }
              ) => {
                const errors =
                  called && !createInProgress && createResult
                    ? createResult.categoryCreate.errors
                    : [];
                return (
                  <NavigatorLink to={categoryShowUrl(parentId)}>
                    {handleCancel => (
                      <CategoryEditPage
                        category={{ description: "", name: "" }}
                        errors={errors}
                        disabled={createInProgress}
                        variant="add"
                        onBack={handleCancel}
                        onSubmit={data =>
                          mutate({ variables: { ...data, parent: parentId } })
                        }
                      />
                    )}
                  </NavigatorLink>
                );
              }}
            </TypedCategoryCreateMutation>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
