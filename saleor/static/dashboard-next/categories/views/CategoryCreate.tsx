import * as React from "react";
import { Redirect } from "react-router-dom";

import { NavigatorLink } from "../../components/Navigator";
import CategoryEditPage from "../components/CategoryEditPage";
import { categoryShowUrl } from "../index";
import {
  categoryCreateMutation,
  TypedCategoryCreateMutation
} from "../mutations";

interface CategoryCreateFormProps {
  parentId: string;
}

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <TypedCategoryCreateMutation mutation={categoryCreateMutation}>
    {(mutate, { called, data: createResult, loading: createInProgress }) => {
      if (
        called &&
        !createInProgress &&
        createResult &&
        createResult.categoryCreate.errors.length === 0
      ) {
        return (
          <Redirect
            to={categoryShowUrl(createResult.categoryCreate.category.id)}
            push={false}
          />
        );
      }
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
              onSubmit={data => mutate({ variables: { ...data, parent: parentId } })}
            />
          )}
        </NavigatorLink>
      );
    }}
  </TypedCategoryCreateMutation>
);
