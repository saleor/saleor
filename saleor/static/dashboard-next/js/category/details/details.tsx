import * as React from "react";
import { Component } from "react";
import { Mutation, Query } from "react-apollo";

import { ConfirmRemoval } from "../../components/modals";
import { DescriptionCard } from "../../components/cards";
import { Navigator } from "../../components/Navigator";
import { categoryDelete } from "../mutations";
import { categoryDetails } from "../queries";
import { pgettext, interpolate, ngettext } from "../../i18n";
import { categoryEditUrl, categoryShowUrl } from "../index";

interface CategoryPropertiesProps {
  categoryId: string;
}

interface CategoryPropertiesState {
  opened: boolean;
}

class CategoryProperties extends Component<
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
      <Navigator>
        {navigate => (
      <Query query={categoryDetails} variables={{ id: categoryId }}>
        {result => (
          <Mutation mutation={categoryDelete} variables={{ id: categoryId }}>
            {deleteCategory => {
              const { data: { category } } = result;
              const handleRemoveAction = async () => {
                await deleteCategory();
                this.handleRemoveButtonClick;
                navigate(
                  categoryShowUrl(
                    category.parent ? category.parent.url : null
                  ),
                  true
                );
              };

              return (
                <>
                  <DescriptionCard
                    description={result.loading ? "" : category.description}
                    editButtonLink={categoryEditUrl(category.id)}
                    handleRemoveButtonClick={this.handleRemoveButtonClick}
                    loading={result.loading}
                    title={result.loading ? "" : category.name}
                  />
                  {!result.loading ? (
                    <ConfirmRemoval
                      onClose={this.handleRemoveButtonClick}
                      onConfirm={handleRemoveAction}
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
          </Mutation>
        )}
      </Query>
        )}
      </Navigator>
    );
  }
}

export default CategoryProperties;
