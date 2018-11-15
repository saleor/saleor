// import { parse as parseQs } from "qs";
// import * as React from "react";
// import { Route, RouteComponentProps, Switch } from "react-router-dom";
// import { WindowTitle } from "../components/WindowTitle";
// import i18n from "../i18n";
// import { CategoryCreateView } from "./views/CategoryCreate";
// import CategoryDetailsView, {
//   CategoryDetailsQueryParams
// } from "./views/CategoryDetails";
// import CategoryList from "./views/CategoryList";

// interface CategoryDetailsRouteParams {
//   id: string;
// }
// const CategoryDetails: React.StatelessComponent<
//   RouteComponentProps<CategoryDetailsRouteParams>
// > = ({ location, match }) => {
//   const qs = parseQs(location.search.substr(1));
//   const params: CategoryDetailsQueryParams = {
//     after: qs.after,
//     before: qs.before
//   };
//   return (
//     <CategoryDetailsView
//       id={decodeURIComponent(match.params.id)}
//       params={params}
//     />
//   );
// };

// interface CategoryCreateRouteParams {
//   id: string;
// }
// const CategoryCreate: React.StatelessComponent<
//   RouteComponentProps<CategoryCreateRouteParams>
// > = ({ match }) => {
//   return (
//     <CategoryCreateView
//       parentId={
//         match.params.id ? decodeURIComponent(match.params.id) : undefined
//       }
//     />
//   );
// };

// const Component = ({ match }) => (
//   <>
//     <WindowTitle title={i18n.t("Categories")} />
//     <Switch>
//       <Route exact path={match.url} component={CategoryList} />
//       <Route exact path={`${match.url}/add/`} component={CategoryCreate} />
//       <Route exact path={`${match.url}/:id/add/`} component={CategoryCreate} />
//       <Route path={`${match.url}/:id/`} component={CategoryDetails} />
//     </Switch>
//   </>
// );

// export const categoryListUrl = "/categories/";
// export const categoryAddUrl = (parentId?: string) => {
//   if (parentId) {
//     return `/categories/${parentId}/add/`;
//   }
//   return `/categories/add/`;
// };
// export const categoryUrl = (id?: string) => {
//   if (id) {
//     return `/categories/${id}/`;
//   }
//   return "/categories/";
// };
// export default Component;
