import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";
import { Component } from "react";
import { Query } from "react-apollo";
import { Redirect } from "react-router-dom";

import { CategoryDeleteDialog } from "./CategoryDeleteDialog";
import { CategoryDetails } from "./CategoryDetails";
import {
  TypedCategoryDeleteMutation,
  categoryDeleteMutation
} from "../mutations";
import { pgettext, interpolate, ngettext } from "../../i18n";
import { categoryEditUrl, categoryShowUrl } from "../index";
import { CategoryPropertiesQuery } from "../gql-types";

interface CategoryPropertiesProps {
  loading: boolean;
  category?: CategoryPropertiesQuery["category"];
}

interface CategoryPropertiesState {
  opened: boolean;
}

export class CategoryProperties extends Component<
  CategoryPropertiesProps,
  CategoryPropertiesState
> {
  state = { opened: false };

  handleRemoveButtonClick = () => {
    this.setState(prevState => ({ opened: !prevState.opened }));
  };

  render() {
    const { category, loading } = this.props;
    const titleFmt = pgettext(
      "Remove category modal title",
      "Remove category %s"
    );
    const contentFmt = pgettext(
      "Remove category modal title",
      "Are you sure you want to remove category <strong>%s</strong>?"
    );
    return (
      <TypedCategoryDeleteMutation
        mutation={categoryDeleteMutation}
        variables={{ id: loading ? "" : category.id }}
      >
        {(deleteCategory, deleteResult) => {
          if (deleteResult && !deleteResult.loading) {
            this.handleRemoveButtonClick();
            return (
              <Redirect
                to={categoryShowUrl(
                  category.parent ? category.parent.id : null
                )}
                push={false}
              />
            );
          }

          return (
            <>
              <CategoryDetails
                description={loading ? "" : category.description}
                editButtonLink={loading ? "" : categoryEditUrl(category.id)}
                handleRemoveButtonClick={this.handleRemoveButtonClick}
                loading={loading}
                title={loading ? "" : category.name}
              />
              {!loading ? (
                <CategoryDeleteDialog
                  onClose={this.handleRemoveButtonClick}
                  onConfirm={() => deleteCategory()}
                  opened={this.state.opened}
                  title={interpolate(titleFmt, [category.name])}
                >
                  <DialogContentText
                    dangerouslySetInnerHTML={{
                      __html: interpolate(contentFmt, [category.name])
                    }}
                  />
                  {category.products &&
                    category.products.totalCount > 0 && (
                      <DialogContentText>
                        {interpolate(
                          ngettext(
                            "There is one product in this category that will be removed.",
                            "There are %s products in this category that will be removed.",
                            category.products.totalCount
                          ),
                          [category.products.totalCount]
                        )}
                      </DialogContentText>
                    )}
                </CategoryDeleteDialog>
              ) : null}
            </>
          );
        }}
      </TypedCategoryDeleteMutation>
    );
  }
}

export default CategoryProperties;
