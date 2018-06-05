import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import { NavigatorLink } from "../../components/Navigator";
import CategoryEditPage from "../components/CategoryEditPage";
import { categoryShowUrl } from "../index";
import {
  categoryUpdateMutation,
  TypedCategoryUpdateMutation
} from "../mutations";
import { categoryDetailsQuery, TypedCategoryDetailsQuery } from "../queries";

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <TypedCategoryDetailsQuery query={categoryDetailsQuery} variables={{ id }}>
    {({ data, loading, error }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }

      return (
        <TypedCategoryUpdateMutation mutation={categoryUpdateMutation}>
          {(
            mutate,
            { called, data: updateResult, loading: updateInProgress }
          ) => {
            if (
              called &&
              !updateInProgress &&
              updateResult &&
              updateResult.categoryUpdate.errors.length === 0
            ) {
              return (
                <Redirect
                  to={categoryShowUrl(updateResult.categoryUpdate.category.id)}
                />
              );
            }
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
                      mutate({
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
);
