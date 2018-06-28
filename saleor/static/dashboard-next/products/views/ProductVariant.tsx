import * as React from "react";

import { productUrl, productVariantEditUrl } from "..";
import * as placeholderImg from "../../../images/placeholder255x255.png";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductVariantPage from "../components/ProductVariantPage";
import { productVariantQuery, TypedProductVariantQuery } from "../queries";

interface ProductUpdateProps {
  variantId: string;
  productId: string;
}

export const ProductVariant: React.StatelessComponent<ProductUpdateProps> = ({
  variantId,
  productId
}) => (
    <Navigator>
      {navigate => {
        return (
          <TypedProductVariantQuery
            query={productVariantQuery}
            variables={{ id: variantId }}
            fetchPolicy="network-only"
          >
            {({ data, loading, error, fetchMore }) => {
              if (error) {
                return <ErrorMessageCard message="Something went wrong" />;
              }

              const variant = data ? data.variant : undefined;

              return (
                <ProductVariantPage
                  loading={loading}
                  placeholderImage={placeholderImg}
                  variant={variant}
                  onBack={() => { navigate(productUrl(productId)); }}
                  onDelete={() => { }}
                  onImageSelect={() => { }}
                  onSubmit={() => {}}
                  onVariantClick={(variantId) => {
                    navigate(productVariantEditUrl(productId, variantId));
                  }}
                />
              );
            }}
          </TypedProductVariantQuery>
        );
      }}
    </Navigator>
  );
export default ProductVariant;
