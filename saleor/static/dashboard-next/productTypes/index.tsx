import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import ProductTypeCreate from "./views/ProductTypeCreate";
import ProductTypeListComponent from "./views/ProductTypeList";
import ProductTypeUpdateComponent from "./views/ProductTypeUpdate";

export const productTypeAddUrl = "/productTypes/add/";
export const productTypeDetailsUrl = (id: string) => `/productTypes/${id}/`;
export const productTypeListUrl = "/productTypes";

const ProductTypeList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const queryString = parseQs(location.search.substr(1));
  const params = {
    after: queryString.after
      ? decodeURIComponent(queryString.after)
      : undefined,
    before: queryString.before
      ? decodeURIComponent(queryString.before)
      : undefined
  };
  return <ProductTypeListComponent params={params} />;
};

interface ProductTypeUpdateRouteParams {
  id: string;
}
const ProductTypeUpdate: React.StatelessComponent<
  RouteComponentProps<ProductTypeUpdateRouteParams>
> = ({ match }) => <ProductTypeUpdateComponent id={match.params.id} />;

export const ProductTypeRouter: React.StatelessComponent<
  RouteComponentProps<any>
> = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={ProductTypeList} />
    <Route exact path={match.url + "/add/"} component={ProductTypeCreate} />
    <Route exact path={match.url + "/:id/"} component={ProductTypeUpdate} />
  </Switch>
);
ProductTypeRouter.displayName = "ProductTypeRouter";
export default ProductTypeRouter;
