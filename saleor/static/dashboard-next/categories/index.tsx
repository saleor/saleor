import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";
import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { categoryAddPath, categoryListPath, categoryPath } from "./urls";
import { CategoryCreateView } from "./views/CategoryCreate";
import CategoryDetailsView, {
  CategoryDetailsQueryParams
} from "./views/CategoryDetails";
import CategoryList from "./views/CategoryList";

interface CategoryDetailsRouteParams {
  id: string;
}
const CategoryDetails: React.StatelessComponent<
  RouteComponentProps<CategoryDetailsRouteParams>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: CategoryDetailsQueryParams = {
    after: qs.after,
    before: qs.before
  };
  return (
    <CategoryDetailsView
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

interface CategoryCreateRouteParams {
  id: string;
}
const CategoryCreate: React.StatelessComponent<
  RouteComponentProps<CategoryCreateRouteParams>
> = ({ match }) => {
  return (
    <CategoryCreateView
      parentId={
        match.params.id ? decodeURIComponent(match.params.id) : undefined
      }
    />
  );
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Categories")} />
    <Switch>
      <Route exact path={categoryListPath} component={CategoryList} />
      <Route exact path={categoryAddPath()} component={CategoryCreate} />
      <Route exact path={categoryAddPath(":id")} component={CategoryCreate} />
      <Route path={categoryPath(":id")} component={CategoryDetails} />
    </Switch>
  </>
);

export default Component;
