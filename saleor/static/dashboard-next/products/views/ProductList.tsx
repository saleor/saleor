import { withStyles } from "@material-ui/core/styles";
import { stringify } from "querystring";
import * as React from "react";

import { productAddUrl, productListUrl, productUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductListCard from "../components/ProductListCard";
import { productListQuery, TypedProductListQuery } from "../queries";

interface ProductListProps {
  params: any;
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

export const ProductList = decorate<ProductListProps>(({ classes, params }) => (
  <div className={classes.root}>
    <Navigator>
      {navigate => {
        const PAGINATE_BY = 20;
        const paginationState =
          params && (params.before || params.after)
            ? params.after
              ? {
                  after: params.after,
                  first: PAGINATE_BY
                }
              : {
                  before: params.before,
                  last: PAGINATE_BY
                }
            : {
                first: PAGINATE_BY
              };
        return (
          <TypedProductListQuery
            query={productListQuery}
            variables={paginationState}
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
                return navigate(
                  productListUrl +
                    "?" +
                    stringify({
                      after: data.products.pageInfo.endCursor
                    }),
                  true
                );
              };
              const loadPreviousPage = () => {
                if (loading) {
                  return;
                }
                return navigate(
                  productListUrl +
                    "?" +
                    stringify({
                      before: data.products.pageInfo.startCursor
                    }),
                  true
                );
              };
              const pageInfo =
                data && data.products && data.products.pageInfo
                  ? {
                      ...data.products.pageInfo,
                      hasNextPage:
                        !!paginationState.before ||
                        data.products.pageInfo.hasNextPage,
                      hasPreviousPage:
                        !!paginationState.after ||
                        data.products.pageInfo.hasPreviousPage
                    }
                  : undefined;
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
                      pageInfo={pageInfo}
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
));
export default ProductList;
