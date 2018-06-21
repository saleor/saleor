import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import ProductListComponent from "./views/ProductList";
import ProductUpdateComponent from "./views/ProductUpdate";

const ProductList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  return <ProductListComponent filters={qs} />;
};

const ProductUpdate: React.StatelessComponent<RouteComponentProps<any>> = ({ match }) => {
  return <ProductUpdateComponent id={match.params.id} />;
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={ProductList} />
    <Route exact path={`${match.url}/:id/`} component={ProductUpdate} />
  </Switch>
);

export function productShowUrl(id: string) {
  return `/products/${id}/`;
}
export function productEditUrl(id: string) {
  return `/products/${id}/edit/`;
}
export function productImageEditUrl(id: string) {
  return `/products/${id}/image/`;
}
export function productStorefrontUrl(slug: string) {
  return `/product/${slug}/`;
}

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
  id: string;
  name: string;
  slug: string;
}

export default Component;
