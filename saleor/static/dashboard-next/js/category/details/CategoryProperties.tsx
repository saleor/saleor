import * as React from "react";
import { Component } from "react";
import { Query } from "react-apollo";
import { Redirect } from "react-router-dom";

import { ConfirmRemoval } from "../../components/modals";
import { CategoryDetails } from "./CategoryDetails";
import { Navigator } from "../../components/Navigator";
import {
  TypedCategoryDeleteMutation,
  categoryDeleteMutation
} from "../mutations";
import { TypedCategoryDetailsQuery, categoryDetailsQuery } from "../queries";
import { pgettext, interpolate, ngettext } from "../../i18n";
import { categoryEditUrl, categoryShowUrl } from "../index";

interface CategoryPropertiesProps {
  categoryId: string;
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
    const { categoryId } = this.props;
    const titleFmt = pgettext(
      "Remove category modal title",
      "Remove category %s"
    );
    const contentFmt = pgettext(
      "Remove category modal title",
      "Are you sure you want to remove category <strong>%s</strong>?"
    );
    return (
      <TypedCategoryDetailsQuery
        query={categoryDetailsQuery}
        variables={{ id: categoryId }}
      >
        {result => (
          <TypedCategoryDeleteMutation
            mutation={categoryDeleteMutation}
            variables={{ id: categoryId }}
          >
            {(deleteCategory, deleteResult) => {
              const { data: { category } } = result;
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
                    description={result.loading ? "" : category.description}
                    editButtonLink={
                      result.loading ? "" : categoryEditUrl(category.id)
                    }
                    handleRemoveButtonClick={this.handleRemoveButtonClick}
                    loading={result.loading}
                    title={result.loading ? "" : category.name}
                  />
                  {!result.loading ? (
                    <ConfirmRemoval
                      onClose={this.handleRemoveButtonClick}
                      onConfirm={() => deleteCategory()}
                      opened={this.state.opened}
                      title={interpolate(titleFmt, [category.name])}
                    >
                      <p
                        dangerouslySetInnerHTML={{
                          __html: interpolate(contentFmt, [category.name])
                        }}
                      />
                      {category.products &&
                        category.products.totalCount > 0 && (
                          <p>
                            {interpolate(
                              ngettext(
                                "There is one product in this category that will be removed.",
                                "There are %s products in this category that will be removed.",
                                category.products.totalCount
                              ),
                              [category.products.totalCount]
                            )}
                          </p>
                        )}
                    </ConfirmRemoval>
                  ) : null}
                </>
              );
            }}
          </TypedCategoryDeleteMutation>
        )}
      </TypedCategoryDetailsQuery>
    );
  }
}

export default CategoryProperties;
