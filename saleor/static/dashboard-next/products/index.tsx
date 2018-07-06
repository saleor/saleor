import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import ProductListComponent from "./views/ProductList";
import ProductUpdateComponent from "./views/ProductUpdate";
import ProductVariantComponent from "./views/ProductVariant";

const ProductList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  return <ProductListComponent filters={qs} />;
};

const ProductUpdate: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <ProductUpdateComponent id={match.params.id} />;
};

const ProductVariant: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return (
    <ProductVariantComponent
      variantId={match.params.variantId}
      productId={match.params.productId}
    />
  );
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={ProductList} />
    <Route exact path={`${match.url}/:id/`} component={ProductUpdate} />
    <Route
      exact
      path={`${match.url}/:productId/variant/:variantId/`}
      component={ProductVariant}
    />
  </Switch>
);

export const productUrl = (id: string) => {
  return `/products/${id}/`;
};

export const productImageEditUrl = (id: string) => {
  return `/products/${id}/image/`;
};

export const productVariantEditUrl = (productId: string, variantId: string) => {
  return `/products/${productId}/variant/${variantId}/`;
};

export const productListUrl = "/products/";

export const productAddUrl = "/products/add/";

export interface AttributeType {
  id: string;
  name: string;
  slug: string;
  values?: Array<{
    name: string;
    slug: string;
  }>;
}

export interface AttributeValueType {
  name: string;
  slug: string;
}

export interface MoneyType {
  amount: number;
  currency: string;
  localized: string;
}

export interface ProductImageType {
  id: string;
  alt: string;
  sortOrder: number;
  url: string;
}

export default Component;
