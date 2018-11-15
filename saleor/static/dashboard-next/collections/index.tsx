// import { parse as parseQs } from "qs";
// import * as React from "react";
// import { Route, RouteComponentProps, Switch } from "react-router-dom";

// import { WindowTitle } from "../components/WindowTitle";
// import i18n from "../i18n";
// import { collectionAddUrl, collectionListUrl, collectionUrl } from "./urls";
// import CollectionCreate from "./views/CollectionCreate";
// import CollectionDetailsView, {
//   CollectionDetailsQueryParams
// } from "./views/CollectionDetails";
// import CollectionListView, {
//   CollectionListQueryParams
// } from "./views/CollectionList";

// const CollectionList: React.StatelessComponent<RouteComponentProps<{}>> = ({
//   location
// }) => {
//   const qs = parseQs(location.search.substr(1));
//   const params: CollectionListQueryParams = {
//     after: qs.after,
//     before: qs.before
//   };
//   return <CollectionListView params={params} />;
// };

// interface CollectionDetailsRouteProps {
//   id: string;
// }
// const CollectionDetails: React.StatelessComponent<
//   RouteComponentProps<CollectionDetailsRouteProps>
// > = ({ location, match }) => {
//   const qs = parseQs(location.search.substr(1));
//   const params: CollectionDetailsQueryParams = {
//     after: qs.after,
//     before: qs.before
//   };
//   return (
//     <CollectionDetailsView
//       id={decodeURIComponent(match.params.id)}
//       params={params}
//     />
//   );
// };

// const Component = () => (
//   <>
//     <WindowTitle title={i18n.t("Collections")} />
//     <Switch>
//       <Route exact path={collectionListUrl} component={CollectionList} />
//       <Route exact path={collectionAddUrl} component={CollectionCreate} />
//       <Route path={collectionUrl(":id")} component={CollectionDetails} />
//     </Switch>
//   </>
// );
// export default Component;
