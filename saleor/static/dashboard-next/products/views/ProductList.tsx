import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { productAddUrl, productUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductListCard from "../components/ProductListCard";
import { productListQuery, TypedProductListQuery } from "../queries";

interface ProductListProps {
  filters: any;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridGap: theme.spacing.unit + "px",
    gridTemplateColumns: "100%",
    [theme.breakpoints.up("md")]: {
      gridGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "3fr 1fr"
    }
  }
}));

export const ProductList = decorate<ProductListProps>(
  ({ classes, filters }) => (
    <div className={classes.root}>
      <Navigator>
        {navigate => {
          return (
            <TypedProductListQuery
              query={productListQuery}
              variables={{ first: 12 }}
              fetchPolicy="network-only"
            >
              {({ data, loading, error, fetchMore }) => {
                if (error) {
                  return <ErrorMessageCard message="Something went wrong" />;
                }
                const loadNextPage = () => {
                  if (loading) {
                    return;
                  }
                  return fetchMore({
                    updateQuery: (previousResult, { fetchMoreResult }) => {
                      return {
                        ...fetchMoreResult,
                        products: {
                          ...fetchMoreResult.products,
                          pageInfo: {
                            ...fetchMoreResult.products.pageInfo,
                            hasPreviousPage: true
                          }
                        }
                      };
                    },
                    variables: {
                      after: data.products.pageInfo.endCursor,
                      first: 12
                    }
                  });
                };
                const loadPreviousPage = () => {
                  if (loading) {
                    return;
                  }
                  return fetchMore({
                    updateQuery: (
                      previousResult,
                      { fetchMoreResult, variables }
                    ) => {
                      return {
                        ...fetchMoreResult,
                        products: {
                          ...fetchMoreResult.products,
                          pageInfo: {
                            ...fetchMoreResult.products.pageInfo,
                            hasNextPage: true
                          }
                        }
                      };
                    },
                    variables: {
                      before: data.products.pageInfo.startCursor,
                      first: undefined,
                      last: 12
                    }
                  });
                };
                return (
                  <>
                    <div>
                      <ProductListCard
                        onAdd={() => navigate(productAddUrl)}
                        disabled={loading}
                        products={
                          data &&
                          data.products !== undefined &&
                          data.products !== null
                            ? data.products.edges.map(p => p.node)
                            : undefined
                        }
                        onNextPage={loadNextPage}
                        onPreviousPage={loadPreviousPage}
                        pageInfo={
                          data && data.products && data.products.pageInfo
                            ? data.products.pageInfo
                            : undefined
                        }
                        onRowClick={id => () => navigate(productUrl(id))}
                      />
                    </div>
                  </>
                );
              }}
            </TypedProductListQuery>
          );
        }}
      </Navigator>
    </div>
  )
);
export default ProductList;
