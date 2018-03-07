import * as React from "react";
import { Route, Switch, RouteComponentProps } from "react-router-dom";
import { parse as parseQs } from "qs";

import CategoryDetails from "./details";
import { CategoryCreateForm, CategoryUpdateForm } from "./form";

const CategoryPaginator: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  return <CategoryDetails id={match.params.id} filters={qs} />;
};
const SubcategoryUpdateForm: React.StatelessComponent<
  RouteComponentProps<any>
> = ({ match }) => {
  return <CategoryUpdateForm id={match.params.id} />;
};

const Component = () => (
  <Switch>
    <Route exact path="/categories/add" component={CategoryCreateForm} />
    <Route
      exact
      path="/categories/:id/edit"
      component={SubcategoryUpdateForm}
    />
    <Route exact path="/categories/:id/add" component={CategoryCreateForm} />
    <Route exact path="/categories/:id" component={CategoryPaginator} />
    <Route path="/categories/" component={CategoryPaginator} />
  </Switch>
);

export default Component;
