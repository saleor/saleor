import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import ProductListComponent from "./views/ProductList";

const ProductList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  return <ProductListComponent filters={qs} />;
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={ProductList} />
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
}

export default Component;
