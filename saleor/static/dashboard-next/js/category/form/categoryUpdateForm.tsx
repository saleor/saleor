import * as React from "react";
import Grid from "material-ui/Grid";
import { Mutation, Query } from "react-apollo";

import { BaseCategoryForm } from "./base";
import { ErrorMessageCard } from "../../components/cards";
import { Navigator } from "../../components/Navigator";
import { categoryDetails } from "../queries";
import { categoryUpdate } from "../mutations";
import { pgettext } from "../../i18n";
import { categoryShowUrl } from "../index";

interface CategoryUpdateFormProps {
  id: string;
}
interface CategoryUpdateResult {
  data: {
    categoryUpdate: {
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

export const CategoryUpdateForm: React.StatelessComponent<
  CategoryUpdateFormProps
> = ({ id }) => (
  <Query query={categoryDetails} variables={{ id }}>
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
            <Navigator>
              {navigate => (
                <Mutation mutation={categoryUpdate} variables={{ id }}>
                  {mutate => (
                    <BaseCategoryForm
                      title={pgettext(
                        "Edit category form card title",
                        "Edit category"
                      )}
                      name={category.name}
                      description={category.description}
                      handleConfirm={formData => async () => {
                        const result = (await mutate({
                          variables: {
                            ...formData,
                            id
                          }
                        })) as CategoryUpdateResult;
                        if (result.data.categoryUpdate.errors.length > 0) {
                          return result.data.categoryUpdate.errors.map(err => (
                            <ErrorMessageCard message={err.message} />
                          ));
                        }
                        navigate(
                          categoryShowUrl(
                            result.data.categoryUpdate.category.id
                          )
                        );
                      }}
                      confirmButtonLabel={pgettext(
                        "Dashboard update action",
                        "Update"
                      )}
                    />
                  )}
                </Mutation>
              )}
            </Navigator>
          </Grid>
        </Grid>
      );
    }}
  </Query>
);
