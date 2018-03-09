import Grid from "material-ui/Grid";
import * as React from "react";
import { Redirect } from "react-router-dom";

import { BaseCategoryForm } from "../components/BaseForm";
import { ErrorMessageCard } from "../../components/cards";
import {
  TypedCategoryCreateMutation,
  categoryCreateMutation
} from "../mutations";
import { pgettext } from "../../i18n";
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
          if (result && !result.loading) {
            if (result.data.categoryCreate.errors.length > 0) {
              return result.data.categoryCreate.errors.map((err, index) => (
                <ErrorMessageCard message={err.message} key={index} />
              ));
            }
            return (
              <Redirect
                to={categoryShowUrl(result.data.categoryCreate.category.id)}
                push={false}
              />
            );
          }
          return (
            <BaseCategoryForm
              title={pgettext("Add category form card title", "Add category")}
              name=""
              description=""
              handleConfirm={formData =>
                mutate({
                  variables: {
                    ...formData,
                    parentId
                  }
                })
              }
              confirmButtonLabel={pgettext("Dashboard create action", "Add")}
            />
          );
        }}
      </TypedCategoryCreateMutation>
    </Grid>
  </Grid>
);
