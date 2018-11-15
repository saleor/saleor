// import { parse as parseQs } from "qs";
// import * as React from "react";
// import { Route, RouteComponentProps, Switch } from "react-router-dom";

// import { WindowTitle } from "../components/WindowTitle";
// import i18n from "../i18n";
// import ProductCreate from "./views/ProductCreate";
// import ProductImageComponent from "./views/ProductImage";
// import ProductListComponent, {
//   ProductListQueryParams
// } from "./views/ProductList";
// import ProductUpdateComponent from "./views/ProductUpdate";
// import ProductVariantComponent from "./views/ProductVariant";
// import ProductVariantCreateComponent from "./views/ProductVariantCreate";

// const ProductList: React.StatelessComponent<RouteComponentProps<any>> = ({
//   location
// }) => {
//   const qs = parseQs(location.search.substr(1));
//   const params: ProductListQueryParams = {
//     after: qs.after,
//     before: qs.before
//   };
//   return <ProductListComponent params={params} />;
// };

// const ProductUpdate: React.StatelessComponent<RouteComponentProps<any>> = ({
//   match
// }) => {
//   return <ProductUpdateComponent id={decodeURIComponent(match.params.id)} />;
// };

// const ProductVariant: React.StatelessComponent<RouteComponentProps<any>> = ({
//   match
// }) => {
//   return (
//     <ProductVariantComponent
//       variantId={decodeURIComponent(match.params.variantId)}
//       productId={decodeURIComponent(match.params.productId)}
//     />
//   );
// };

// const ProductImage: React.StatelessComponent<RouteComponentProps<any>> = ({
//   match
// }) => {
//   return (
//     <ProductImageComponent
//       imageId={decodeURIComponent(match.params.imageId)}
//       productId={decodeURIComponent(match.params.productId)}
//     />
//   );
// };

// const ProductVariantCreate: React.StatelessComponent<
//   RouteComponentProps<any>
// > = ({ match }) => {
//   return (
//     <ProductVariantCreateComponent
//       productId={decodeURIComponent(match.params.id)}
//     />
//   );
// };

// const Component = ({ match }) => (
//   <>
//     <WindowTitle title={i18n.t("Products")} />
//     <Switch>
//       <Route exact path={match.url} component={ProductList} />
//       <Route exact path={`${match.url}/add/`} component={ProductCreate} />
//       <Route exact path={`${match.url}/:id/`} component={ProductUpdate} />
//       <Route
//         exact
//         path={`${match.url}/:id/variant/add/`}
//         component={ProductVariantCreate}
//       />
//       <Route
//         exact
//         path={`${match.url}/:productId/variant/:variantId/`}
//         component={ProductVariant}
//       />
//       <Route
//         exact
//         path={`${match.url}/:productId/image/:imageId/`}
//         component={ProductImage}
//       />
//     </Switch>
//   </>
// );

// export const productUrl = (id: string) => {
//   return `/products/${id}/`;
// };

// export const productVariantAddUrl = (productId: string) => {
//   return `/products/${productId}/variant/add/`;
// };

// export const productVariantEditUrl = (productId: string, variantId: string) => {
//   return `/products/${productId}/variant/${variantId}/`;
// };

// export const productImageUrl = (productId: string, imageId: string) =>
//   `/products/${productId}/image/${imageId}/`;

// export const productListUrl = "/products/";
// export const productAddUrl = "/products/add/";

// export interface AttributeType {
//   id: string;
//   name: string;
//   slug: string;
//   values?: Array<{
//     name: string;
//     slug: string;
//   }>;
// }

// export interface AttributeValueType {
//   name: string;
//   slug: string;
// }

// export interface MoneyType {
//   amount: number;
//   currency: string;
// }

// export interface ProductImageType {
//   id: string;
//   sortOrder: number;
//   url: string;
// }

// export default Component;
