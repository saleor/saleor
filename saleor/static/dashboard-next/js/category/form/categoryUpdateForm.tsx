import * as React from "react";
import { Component, Fragment } from "react";
import Grid from "material-ui/Grid";
import { graphql, Mutation, Query } from "react-apollo";

import { BaseCategoryForm } from "./base";
import { categoryDetails } from "../queries";
import { categoryUpdate } from "../mutations";
import { pgettext } from "../../i18n";

interface CategoryUpdateFormProps {
  id: string;
}

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <Query query={categoryDetails}>
    {({ data, loading }) => {
      if (loading) {
        return;
      }
      const { categories } = data;

      return categories.map(category => (
        <Grid container spacing={16}>
          <Grid item xs={12} md={9}>
            <Mutation mutation={categoryUpdate} variables={{ id }}>
              {mutate => (
                <BaseCategoryForm
                  title={pgettext(
                    "Edit category form card title",
                    "Edit category"
                  )}
                  name={category.name}
                  description={category.description}
                  handleConfirm={formData => {
                    mutate({
                      variables: {
                        ...formData,
                        id
                      }
                    });
                  }}
                  confirmButtonLabel={pgettext(
                    "Dashboard update action",
                    "Update"
                  )}
                />
              )}
            </Mutation>
          </Grid>
        </Grid>
      ));
    }}
  </Query>
);
