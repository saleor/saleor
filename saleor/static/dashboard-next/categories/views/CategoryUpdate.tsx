import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator, { NavigatorLink } from "../../components/Navigator";
import { CategoryUpdateMutation } from "../../gql-types";
import i18n from "../../i18n";
import CategoryEditPage from "../components/CategoryEditPage";
import { categoryShowUrl } from "../index";
import {
  TypedCategoryUpdateMutation
} from "../mutations";
import { categoryDetailsQuery, TypedCategoryDetailsQuery } from "../queries";

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => (
          <TypedCategoryDetailsQuery
            query={categoryDetailsQuery}
            variables={{ id }}
          >
            {({ data, loading, error }) => {
              if (error) {
                return <ErrorMessageCard message={error.message} />;
              }
              const handleUpdateSuccess = (data: CategoryUpdateMutation) => {
                if (data.categoryUpdate.errors.length === 0) {
                  pushMessage({ text: i18n.t("Category updated") });
                  navigate(categoryShowUrl(data.categoryUpdate.category.id));
                }
              };
              return (
                <TypedCategoryUpdateMutation onCompleted={handleUpdateSuccess}>
                  {(
                    updateCategory,
                    { called, data: updateResult, loading: updateInProgress }
                  ) => {
                    const errors =
                      called && !updateInProgress && updateResult
                        ? updateResult.categoryUpdate.errors
                        : [];
                    return (
                      <NavigatorLink to={categoryShowUrl(id)}>
                        {handleCancel => (
                          <CategoryEditPage
                            category={data ? data.category : undefined}
                            errors={errors}
                            disabled={updateInProgress || loading}
                            variant="edit"
                            onBack={handleCancel}
                            onSubmit={data =>
                              updateCategory({
                                variables: { ...data, id }
                              })
                            }
                          />
                        )}
                      </NavigatorLink>
                    );
                  }}
                </TypedCategoryUpdateMutation>
              );
            }}
          </TypedCategoryDetailsQuery>
        )}
      </Navigator>
    )}
  </Messages>
);
