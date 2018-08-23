import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import ProductTypeListComponent from "./views/ProductTypeList";
import ProductTypeUpdateComponent from "./views/ProductTypeUpdate";

export const productTypeListUrl = "/productTypes";
export const productTypeDetailsUrl = (id: string) => `/productTypes/${id}/`;

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
    <Route exact path={match.url + "/:id/"} component={ProductTypeUpdate} />
  </Switch>
);
ProductTypeRouter.displayName = "ProductTypeRouter";
export default ProductTypeRouter;
