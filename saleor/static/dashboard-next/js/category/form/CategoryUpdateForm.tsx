import Grid from "material-ui/Grid";
import * as React from "react";
import { Redirect } from "react-router-dom";

import { BaseCategoryForm } from "./base";
import { ErrorMessageCard } from "../../components/cards";
import { Navigator } from "../../components/Navigator";
import { TypedCategoryDetailsQuery, categoryDetailsQuery } from "../queries";
import {
  TypedCategoryUpdateMutation,
  categoryUpdateMutation
} from "../mutations";
import { pgettext } from "../../i18n";
import { categoryShowUrl } from "../index";

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <TypedCategoryDetailsQuery query={categoryDetailsQuery} variables={{ id }}>
    {({ data, loading, error }) => {
      if (error) {
        console.error(error.message);
        return <ErrorMessageCard message={error.message} />;
      }
      if (loading) {
        return <span>loading</span>;
      }
      const { category } = data;

      return (
        <Grid container spacing={16}>
          <Grid item xs={12} md={9}>
            <TypedCategoryUpdateMutation mutation={categoryUpdateMutation}>
              {(mutate, result) => {
                if (result && !result.loading) {
                  if (result.data.categoryUpdate.errors.length > 0) {
                    return result.data.categoryUpdate.errors.map(err => (
                      <ErrorMessageCard message={err.message} />
                    ));
                  }
                  return (
                    <Redirect
                      to={categoryShowUrl(
                        result.data.categoryUpdate.category.id
                      )}
                    />
                  );
                }
                return (
                  <BaseCategoryForm
                    title={pgettext(
                      "Edit category form card title",
                      "Edit category"
                    )}
                    name={category.name}
                    description={category.description}
                    handleConfirm={formData =>
                      mutate({
                        variables: {
                          ...formData,
                          id
                        }
                      })
                    }
                    confirmButtonLabel={pgettext(
                      "Dashboard update action",
                      "Update"
                    )}
                  />
                );
              }}
            </TypedCategoryUpdateMutation>
          </Grid>
        </Grid>
      );
    }}
  </TypedCategoryDetailsQuery>
);
