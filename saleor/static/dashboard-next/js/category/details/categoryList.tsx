import * as React from "react";
import { Component } from "react";
import { graphql } from "react-apollo";
import { parse as parseQs } from "qs";

import { ListCard } from "../../components/cards";
import { categoryChildren, rootCategoryChildren } from "../queries";
import { createQueryString } from "../../misc";
import { pgettext } from "../../i18n";
import { TableRow, TableCell } from "material-ui";
import { Link } from "react-router-dom";
import { Navigator } from "../../components/Navigator";
import { Table } from "../../components/Table";
import { Skeleton } from "../../components/Skeleton";

const tableHeaders = [
  {
    label: pgettext("Category list table header name", "Name"),
    name: "name"
  },
  {
    label: pgettext("Category list table header description", "Description"),
    name: "description",
    wide: true
  }
];
const PAGINATE_BY = 4;

const feederOptions = {
  options: props => ({
    variables: {
      id: props.categoryId,
      first: props.filters.after
        ? PAGINATE_BY
        : props.filters.before ? null : PAGINATE_BY,
      last: props.filters.before ? PAGINATE_BY : null,
      before: props.filters.before,
      after: props.filters.after
    },
    fetchPolicy: "network-only"
  })
};
const categoryListFeeder = graphql(categoryChildren, feederOptions);
const rootCategoryListFeeder = graphql(rootCategoryChildren, feederOptions);

interface BaseCategoryListProps {
  categories: {
    edges: Array<any>;
    pageInfo: {
      hasNextPage: boolean;
      hasPreviousPage: boolean;
      startCursor: string;
      endCursor: string;
    };
  };
  label: string;
  loading: boolean;
  filters: {
    first?: string;
    last?: string;
    after?: string;
    before?: string;
  };
}

class BaseCategoryList extends Component<BaseCategoryListProps> {
  handleAddAction = () => {
    // this.props.history.push("add");
  };

  handleRowClick = id => {
    // return () => this.props.history.push(`/categories/${id}/`);
  };

  render() {
    const { label, loading, categories, filters } = this.props;
    const pageInfo = {
      hasPreviousPage: filters.after
        ? true
        : categories.pageInfo.hasPreviousPage,
      hasNextPage: filters.before ? true : categories.pageInfo.hasNextPage
    };
    return (
      <Navigator>
        {navigate => (
          <ListCard
            addActionLabel="Add"
            displayLabel={true}
            handleAddAction={this.handleAddAction}
            label={label}
          >
            <Table
              headers={tableHeaders}
              onNextPage={() =>
                navigate(`?after=${categories.pageInfo.endCursor}`)
              }
              onPreviousPage={() =>
                navigate(`?before=${categories.pageInfo.startCursor}`)
              }
              page={pageInfo}
            >
              {loading ? (
                <TableRow>
                  {tableHeaders.map(header => (
                    <TableCell key={header.name}>
                      <Skeleton style={{ width: "80%" }} />
                    </TableCell>
                  ))}
                </TableRow>
              ) : (
                categories.edges.map(({ node }) => (
                  <TableRow
                    key={node.id}
                    onClick={() => navigate(`/categories/${node.id}/`)}
                  >
                    {tableHeaders.map(header => (
                      <TableCell key={header.name}>
                        {node[header.name]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </Table>
          </ListCard>
        )}
      </Navigator>
    );
  }
}

interface CategoryListComponentProps {
  data: {
    loading: boolean;
    category: {
      children: {
        edges: Array<any>;
        pageInfo: {
          hasNextPage: boolean;
          hasPreviousPage: boolean;
          startCursor: string;
          endCursor: string;
        };
      };
    };
  };
  filters: {
    first?: string;
    last?: string;
    after?: string;
    before?: string;
  };
}

const CategoryListComponent: React.StatelessComponent<
  CategoryListComponentProps
> = props => {
  const { data } = props;
  const categories = data.category
    ? data.category.children
    : {
        edges: [],
        pageInfo: {
          hasNextPage: false,
          hasPreviousPage: false,
          startCursor: "",
          endCursor: ""
        }
      };
  return (
    <BaseCategoryList
      categories={categories}
      label={pgettext("Title of the subcategories list", "Subcategories")}
      loading={data.loading}
      filters={props.filters}
    />
  );
};
const CategoryList = categoryListFeeder(CategoryListComponent);

interface RootCategoryListComponentProps {
  data: {
    loading: boolean;
    categories: {
      edges: Array<any>;
      pageInfo: {
        hasNextPage: boolean;
        hasPreviousPage: boolean;
        startCursor: string;
        endCursor: string;
      };
    };
  };
  filters: {
    first?: string;
    last?: string;
    after?: string;
    before?: string;
  };
}

const RootCategoryListComponent: React.StatelessComponent<
  RootCategoryListComponentProps
> = props => {
  const { data } = props;
  const categories = data.categories || {
    edges: [],
    pageInfo: {
      hasNextPage: false,
      hasPreviousPage: false,
      startCursor: "",
      endCursor: ""
    }
  };
  return (
    <BaseCategoryList
      categories={categories}
      label={pgettext("Title of the categories list", "Categories")}
      loading={data.loading}
      filters={props.filters}
    />
  );
};
const RootCategoryList = rootCategoryListFeeder(RootCategoryListComponent);

export { CategoryList, RootCategoryList };
