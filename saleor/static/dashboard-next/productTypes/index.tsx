import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  productTypeAddPath,
  productTypeListPath,
  ProductTypeListUrlQueryParams,
  productTypePath,
  ProductTypeUrlQueryParams
} from "./urls";
import ProductTypeCreate from "./views/ProductTypeCreate";
import ProductTypeListComponent from "./views/ProductTypeList";
import ProductTypeUpdateComponent from "./views/ProductTypeUpdate";

const ProductTypeList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: ProductTypeListUrlQueryParams = qs;
  return <ProductTypeListComponent params={params} />;
};

interface ProductTypeUpdateRouteParams {
  id: string;
}
const ProductTypeUpdate: React.StatelessComponent<
  RouteComponentProps<ProductTypeUpdateRouteParams>
> = ({ match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: ProductTypeUrlQueryParams = qs;

  return (
    <ProductTypeUpdateComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

export const ProductTypeRouter: React.StatelessComponent<
  RouteComponentProps<any>
> = () => (
  <>
    <WindowTitle title={i18n.t("Product types")} />
    <Switch>
      <Route exact path={productTypeListPath} component={ProductTypeList} />
      <Route exact path={productTypeAddPath} component={ProductTypeCreate} />
      <Route path={productTypePath(":id")} component={ProductTypeUpdate} />
    </Switch>
  </>
);
ProductTypeRouter.displayName = "ProductTypeRouter";
export default ProductTypeRouter;
