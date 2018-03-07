import * as React from "react";
import Grid from "material-ui/Grid";
import { Mutation } from "react-apollo";

import { BaseCategoryForm } from "./base";
import { ErrorMessageCard } from "../../components/cards";
import { Navigator } from "../../components/Navigator";
import { categoryCreate } from "../mutations";
import { pgettext } from "../../i18n";

type CategoryCreateFormProps = {
  parentId: string;
};
interface CategoryCreateResult {
  data: {
    categoryCreate: {
      errors: Array<{
        field: string;
        message: string;
      }>;
      category: {
        id: string;
        name: string;
        description: string;
        parent: {
          id?: string;
        };
      };
    };
  };
}

export const CategoryCreateForm: React.StatelessComponent<
  CategoryCreateFormProps
> = ({ parentId }) => (
  <Grid container spacing={16}>
    <Grid item xs={12} md={9}>
      <Navigator>
        {navigate => (
          <Mutation mutation={categoryCreate} variables={{ parentId }}>
            {mutate => (
              <BaseCategoryForm
                title={pgettext("Add category form card title", "Add category")}
                name=""
                description=""
                handleConfirm={formData => async () => {
                  const result = (await mutate({
                    variables: {
                      ...formData
                    }
                  })) as CategoryCreateResult;
                  if (result.data.categoryCreate.errors.length > 0) {
                    return result.data.categoryCreate.errors.map(err => (
                      <ErrorMessageCard message={err.message} />
                    ));
                  }
                  navigate(
                    `/categories/${result.data.categoryCreate.category.id}`,
                    true
                  );
                }}
                confirmButtonLabel={pgettext("Dashboard create action", "Add")}
              />
            )}
          </Mutation>
        )}
      </Navigator>
    </Grid>
  </Grid>
);
