import * as React from "react";
import { Component } from "react";
import Grid from "material-ui/Grid";
import { Mutation } from "react-apollo";

import { BaseCategoryForm } from "./base";
import { categoryCreate } from "../mutations";
import { pgettext } from "../../i18n";

type CategoryCreateFormProps = {
  parentId: string;
};

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <Grid container spacing={16}>
    <Grid item xs={12} md={9}>
      <Mutation mutation={categoryCreate} variables={{ parentId }}>
        {mutate => (
          <BaseCategoryForm
            title={pgettext("Add category form card title", "Add category")}
            name=""
            description=""
            handleConfirm={formData => {
              mutate({
                variables: {
                  ...formData,
                  parentId: parentId
                }
              });
            }}
            confirmButtonLabel={pgettext("Dashboard create action", "Add")}
          />
        )}
      </Mutation>
    </Grid>
  </Grid>
);
