import Card from "material-ui/Card";
import * as React from "react";
import { Redirect } from "react-router-dom";

import { NavigatorLink } from "../../components/Navigator";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";
import BaseCategoryForm from "../components/BaseForm";
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
    {(mutate, { called, data, loading }) => {
      if (called && !loading && data.categoryCreate.errors.length === 0) {
        return (
          <Redirect
            to={categoryShowUrl(data.categoryCreate.category.id)}
            push={false}
          />
        );
      }
      return (
        <NavigatorLink to={categoryShowUrl(parentId)}>
          {handleCancel => (
            <Card style={{ maxWidth: 750 }}>
              <PageHeader
                onCancel={handleCancel}
                title={i18n.t("Add category", { context: "title" })}
              />
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
                errors={called && !loading ? data.categoryCreate.errors : []}
              />
            </Card>
          )}
        </NavigatorLink>
      );
    }}
  </TypedCategoryCreateMutation>
);
