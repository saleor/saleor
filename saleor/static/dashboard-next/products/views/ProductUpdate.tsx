import * as React from "react";

import * as placeholderImg from "../../../images/placeholder255x255.png";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductUpdatePage from "../components/ProductUpdatePage";
import { productDetailsQuery, TypedProductDetailsQuery } from "../queries";
import { productVariantEditUrl } from "../index";

interface ProductUpdateProps {
  id: string;
}

export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
  id
}) => (
  <Navigator>
    {navigate => {
      return (
        <TypedProductDetailsQuery
          query={productDetailsQuery}
          variables={{ id }}
          fetchPolicy="network-only"
        >
          {({ data, loading, error, fetchMore }) => {
            if (error) {
              return <ErrorMessageCard message="Something went wrong" />;
            }

            const product = data ? data.product : undefined;
            const allCollections =
              data && data.collections
                ? data.collections.edges.map(edge => edge.node)
                : [];
            const allCategories =
              data && data.categories
                ? data.categories.edges.map(edge => edge.node)
                : [];

            return (
              <ProductUpdatePage
                categories={allCategories}
                collections={allCollections}
                images={
                  product ? product.images.edges.map(edge => edge.node) : undefined
                }
                placeholderImage={placeholderImg}
                product={product}
                productCollections={
                  product
                  ? product.collections.edges.map(edge => edge.node)
                  : undefined
                }
                variants={
                  product ? product.variants.edges.map(edge => edge.node) : undefined
                }
                onBack={() => { window.history.back() }}
                onDelete={() => {}}
                onProductShow={() => {
                  if (product) {
                    window.open(product.url);
                  }
                }}
                onSubmit={() => {}}
                onVariantAdd={() => {}}
                onVariantShow={
                  (variantId) => {
                    if (product) {
                      navigate(productVariantEditUrl(product.id, variantId))
                    }
                  }
                }
              />
            );
          }}
        </TypedProductDetailsQuery>
      );
    }}
  </Navigator>
);
export default ProductUpdate;
