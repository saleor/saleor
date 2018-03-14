import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";
import { Component } from "react";
import { Query } from "react-apollo";
import { Redirect } from "react-router-dom";

import CategoryDeleteDialog from "./CategoryDeleteDialog";
import CategoryDetails from "./CategoryDetails";
import {
  TypedCategoryDeleteMutation,
  categoryDeleteMutation
} from "../mutations";
import { categoryEditUrl, categoryShowUrl } from "../index";
import { CategoryPropertiesQuery } from "../gql-types";
import i18n from "../../i18n";

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

    return (
      <TypedCategoryDeleteMutation
        mutation={categoryDeleteMutation}
        variables={{ id: (category && category.id) || "" }}
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
                description={category && category.description}
                editButtonLink={category && categoryEditUrl(category.id)}
                handleRemoveButtonClick={this.handleRemoveButtonClick}
                title={category && category.name}
              />
              {!loading ? (
                <CategoryDeleteDialog
                  onClose={this.handleRemoveButtonClick}
                  onConfirm={() => deleteCategory()}
                  opened={this.state.opened}
                >
                  <DialogContentText
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "Are you sure you want to remove <strong>{{name}}</strong>?",
                        { name: category.name }
                      )
                    }}
                  />
                  {category.products &&
                    category.products.totalCount > 0 && (
                      <DialogContentText>
                        {i18n.t(
                          "There are {{count}} product(s) in this category that will also be removed.",
                          { count: category.products.totalCount }
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
