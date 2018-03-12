import Grid from "material-ui/Grid";
import * as React from "react";
import { Redirect } from "react-router-dom";

import { BaseCategoryForm } from "../components/BaseForm";
import { ErrorMessageCard } from "../../components/cards";
import {
  TypedCategoryCreateMutation,
  categoryCreateMutation
} from "../mutations";
import i18n from "../../i18n";
import { categoryShowUrl } from "../index";

type CategoryCreateFormProps = {
  parentId: string;
};

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <Grid container spacing={16}>
    <Grid item xs={12} md={9}>
      <TypedCategoryCreateMutation mutation={categoryCreateMutation}>
        {(mutate, result) => {
          if (
            result &&
            !result.loading &&
            result.data.categoryCreate.errors.length === 0
          ) {
            return (
              <Redirect
                to={categoryShowUrl(result.data.categoryCreate.category.id)}
                push={false}
              />
            );
          }
          return (
            <BaseCategoryForm
              confirmButtonLabel={i18n.t("Add", { context: "button" })}
              description=""
              handleConfirm={formData =>
                mutate({
                  variables: {
                    ...formData,
                    parentId
                  }
                })
              }
              name=""
              title={i18n.t("Add category", { context: "title" })}
              errors={
                result && !result.loading
                  ? result.data.categoryCreate.errors
                  : []
              }
            />
          );
        }}
      </TypedCategoryCreateMutation>
    </Grid>
  </Grid>
);
