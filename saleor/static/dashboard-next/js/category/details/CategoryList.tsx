import Table, {
  TableRow,
  TableCell,
  TableHead,
  TableBody,
  TableFooter
} from "material-ui/Table";
import * as React from "react";
import { Component } from "react";
import { graphql } from "react-apollo";

import { CategoryListCard } from "./CategoryListCard";
import { Navigator } from "../../components/Navigator";
import { Skeleton } from "../../components/Skeleton";
import { categoryAddUrl, categoryShowUrl } from "../index";
import {
  TypedCategoryChildrenQuery,
  TypedRootCategoryChildrenQuery,
  categoryChildrenQuery,
  rootCategoryChildrenQuery
} from "../queries";
import { gettext, pgettext } from "../../i18n";
import TablePagination from "../../components/TablePagination";

const PAGINATE_BY = 4;

interface BaseCategoryListProps {
  categoryId?: string;
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
  render() {
    const { label, loading, categories, filters, categoryId } = this.props;
    const pageInfo = {
      hasPreviousPage: filters.after
        ? true
        : categories.pageInfo.hasPreviousPage,
      hasNextPage: filters.before ? true : categories.pageInfo.hasNextPage
    };
    return (
      <Navigator>
        {navigate => (
          <CategoryListCard
            addActionLabel={gettext("Create category")}
            addActionLink={categoryAddUrl(categoryId)}
            label={label}
          >
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    {pgettext("Category list table header name", "Name")}
                  </TableCell>
                  <TableCell>
                    {pgettext(
                      "Category list table header description",
                      "Description"
                    )}
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell>
                      <Skeleton style={{ width: "60%" }} />
                    </TableCell>
                    <TableCell>
                      <Skeleton style={{ width: "80%" }} />
                    </TableCell>
                  </TableRow>
                ) : (
                  categories.edges.map(
                    ({ node: { id, name, description } }) => (
                      <TableRow
                        hover
                        key={id}
                        onClick={() => navigate(categoryShowUrl(id))}
                      >
                        <TableCell>{name}</TableCell>
                        <TableCell>{description}</TableCell>
                      </TableRow>
                    )
                  )
                )}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TablePagination
                    colSpan={5}
                    hasNextPage={pageInfo.hasNextPage}
                    hasPreviousPage={pageInfo.hasPreviousPage}
                    onNextPage={() =>
                      navigate(`?after=${categories.pageInfo.endCursor}`)
                    }
                    onPreviousPage={() =>
                      navigate(`?before=${categories.pageInfo.startCursor}`)
                    }
                  />
                </TableRow>
              </TableFooter>
            </Table>
          </CategoryListCard>
        )}
      </Navigator>
    );
  }
}

interface CategoryListProps {
  categoryId: string;
  filters: {
    first?: string;
    last?: string;
    after?: string;
    before?: string;
  };
}

export const CategoryList: React.StatelessComponent<CategoryListProps> = ({
  categoryId,
  filters
}) => (
  <TypedCategoryChildrenQuery
    query={categoryChildrenQuery}
    variables={{
      id: categoryId,
      first: filters.after ? PAGINATE_BY : filters.before ? null : PAGINATE_BY,
      last: filters.before ? PAGINATE_BY : null,
      before: filters.before,
      after: filters.after
    }}
  >
    {({ data, loading }) => {
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
          loading={loading}
          filters={filters}
          categoryId={categoryId}
        />
      );
    }}
  </TypedCategoryChildrenQuery>
);

interface RootCategoryListProps {
  filters: {
    first?: string;
    last?: string;
    after?: string;
    before?: string;
  };
}

export const RootCategoryList: React.StatelessComponent<
  RootCategoryListProps
> = ({ filters }) => (
  <TypedRootCategoryChildrenQuery
    query={rootCategoryChildrenQuery}
    variables={{
      first: filters.after ? PAGINATE_BY : filters.before ? null : PAGINATE_BY,
      last: filters.before ? PAGINATE_BY : null,
      before: filters.before,
      after: filters.after
    }}
  >
    {({ data, loading }) => {
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
          loading={loading}
          filters={filters}
        />
      );
    }}
  </TypedRootCategoryChildrenQuery>
);
