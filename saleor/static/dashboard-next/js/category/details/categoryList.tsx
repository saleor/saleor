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
import { Table } from "../../components/table";

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
  options: props => {
    const options = {
      variables: {
        id: props.categoryId
      },
      fetchPolicy: "network-only"
    };
    const qs = parseQs("");
    let variables;
    switch (qs.action) {
      case "prev":
        variables = {
          after: null,
          before: qs.firstCursor,
          first: null,
          last: PAGINATE_BY
        };
        break;
      case "next":
        variables = {
          after: qs.lastCursor,
          before: null,
          first: PAGINATE_BY,
          last: null
        };
        break;
      default:
        variables = {
          after: qs.lastCursor,
          before: null,
          first: PAGINATE_BY,
          last: null
        };
        break;
    }
    options.variables = { ...options.variables, ...variables };
    return options;
  }
};
const categoryListFeeder = graphql(categoryChildren, feederOptions);
const rootCategoryListFeeder = graphql(rootCategoryChildren, feederOptions);

interface BaseCategoryListProps {
  categories: {
    edges: Array<any>;
    pageInfo: {
      hasNextPage: boolean;
      hasPreviousPage: boolean;
    };
  };
  location: any;
  label: string;
}

class BaseCategoryList extends Component<BaseCategoryListProps> {
  handleAddAction = () => {
    // this.props.history.push("add");
  };

  handleChangePage = event => {
    // this.props.history.push({
    //   search: createQueryString(this.props.location.search, {
    //     action,
    //     currentPage,
    //     firstCursor,
    //     lastCursor
    //   })
    // });
  };

  handleRowClick = id => {
    // return () => this.props.history.push(`/categories/${id}/`);
  };

  render() {
    const { label, categories } = this.props;
    const firstCursor =
      categories.edges.length > 0 ? categories.edges[0].cursor : "";
    const lastCursor =
      categories.edges.length > 0 ? categories.edges.slice(-1)[0].cursor : "";
    const qs = parseQs("");
    return (
      <ListCard
        addActionLabel="Add"
        displayLabel={true}
        handleAddAction={this.handleAddAction}
        label={label}
      >
        <Table
          handleRowClick={this.handleRowClick}
          headers={tableHeaders}
          onNextPage={this.handleChangePage}
          onPreviousPage={this.handleChangePage}
          page={categories.pageInfo}
        >
          {categories.edges.map(({ node }) => (
            <TableRow key={node.id}>
              {tableHeaders.map(header => (
                <TableCell key={header.name}>{node[header.name]}</TableCell>
              ))}
            </TableRow>
          ))}
        </Table>
      </ListCard>
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
        };
      };
    };
  };
  location: any;
}

const CategoryListComponent: React.StatelessComponent<
  CategoryListComponentProps
> = props => {
  const { data } = props;
  const categories = data.category
    ? data.category.children
    : { edges: [], pageInfo: { hasNextPage: false, hasPreviousPage: false } };
  return (
    <div>
      {data.loading ? (
        <span>loading</span>
      ) : (
        <BaseCategoryList
          categories={categories}
          label={pgettext("Title of the subcategories list", "Subcategories")}
          location={props.location}
        />
      )}
    </div>
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
      };
    };
  };
  location: any;
}

const RootCategoryListComponent: React.StatelessComponent<
  RootCategoryListComponentProps
> = props => {
  const { data } = props;
  const categories = data.categories || {
    edges: [],
    pageInfo: { hasNextPage: false, hasPreviousPage: false }
  };
  return (
    <div>
      {data.loading ? (
        <span>loading</span>
      ) : (
        <BaseCategoryList
          categories={categories}
          label={pgettext("Title of the categories list", "Categories")}
          location={props.location}
        />
      )}
    </div>
  );
};
const RootCategoryList = rootCategoryListFeeder(RootCategoryListComponent);

export { CategoryList, RootCategoryList };
