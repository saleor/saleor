// import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";
import { CategoryCreateView } from "./views/CategoryCreate";
import CategoryList from "./views/CategoryList";

// import { CategoryCreateForm } from "./views/CategoryCreate";
// import CategoryDetails from "./views/CategoryDetails";
// import { CategoryUpdateForm } from "./views/CategoryUpdate";

// const CategoryPaginator: React.StatelessComponent<RouteComponentProps<any>> = ({
//   location,
//   match
// }) => {
//   const qs = parseQs(location.search.substr(1));
//   const params = {
//     after: qs.after,
//     before: qs.before
//   };
//   return <CategoryDetails id={match.params.id} params={params} />;
// };
const CategoryCreate: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <CategoryCreateView parentId={match.params.id} />;
};
// const SubcategoryUpdateForm: React.StatelessComponent<
//   RouteComponentProps<any>
// > = ({ match }) => {
//   return <CategoryUpdateForm id={match.params.id} />;
// };

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={CategoryList} />
    <Route exact path={`${match.url}/add/`} component={CategoryCreate} />
    <Route exact path={`${match.url}/:id/add/`} component={null} />
    <Route exact path={`${match.url}/:id/`} component={null} />
  </Switch>
);

export const categoryListUrl = "/categories/";
export const categoryAddUrl = (parentId?: string) => {
  if (parentId) {
    return `/categories/${parentId}/add/`;
  }
  return `/categories/add/`;
};
export const categoryUrl = (id?: string) => {
  return `/categories/${id ? `${id}/` : ""}`;
};
export default Component;
