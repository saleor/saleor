import * as React from "react";

import { arrayMove } from "react-sortable-hoc";
import * as placeholderImg from "../../../images/placeholder255x255.png";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import ProductUpdatePage from "../components/ProductUpdatePage";
import ProductUpdateOperations from "../containers/ProductUpdateOperations";
import { productListUrl, productVariantEditUrl } from "../index";
import { productDetailsQuery, TypedProductDetailsQuery } from "../queries";

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
            const images =
              data && data.product
                ? data.product.images.edges.map(edge => edge.node)
                : undefined;

            return (
              <ProductUpdateOperations product={product}>
                {({
                  createProductImage,
                  deleteProduct,
                  error,
                  loading,
                  reorderProductImages,
                  updateProduct
                }) => {
                  return (
                    <ProductUpdatePage
                      categories={allCategories}
                      collections={allCollections}
                      disabled={loading}
                      saveButtonBarState={loading ? "loading" : "idle"}
                      images={images}
                      placeholderImage={placeholderImg}
                      product={product}
                      productCollections={
                        product && product.collections
                          ? product.collections.edges.map(edge => edge.node)
                          : undefined
                      }
                      variants={
                        product && product.variants
                          ? product.variants.edges.map(edge => edge.node)
                          : undefined
                      }
                      onBack={() => {
                        navigate(productListUrl);
                      }}
                      onDelete={deleteProduct}
                      onProductShow={() => {
                        if (product) {
                          window.open(product.url);
                        }
                      }}
                      onImageReorder={({ newIndex, oldIndex }) => {
                        if (product) {
                          let ids = images.map(image => image.id);
                          ids = arrayMove(ids, oldIndex, newIndex);
                          reorderProductImages({
                            imagesIds: ids,
                            productId: product.id
                          });
                        }
                      }}
                      onSubmit={data => {
                        if (product) {
                          const attributes = product.attributes
                            .map(item => ({
                              slug: item.attribute.slug,
                              values: item.attribute.values
                            }))
                            .map(({ slug, values }) => {
                              const valueSlug = data[slug];
                              const value = values.filter(
                                item => item.slug === valueSlug
                              );
                              return {
                                slug,
                                value: value ? value[0].name : valueSlug
                              };
                            });

                          updateProduct({
                            attributes,
                            availableOn:
                              data.availableOn !== "" ? data.availableOn : null,
                            category: data.category,
                            chargeTaxes: data.chargeTaxes,
                            collections: data.collections,
                            description: data.description,
                            id: product.id,
                            isFeatured: data.featured,
                            isPublished: data.available,
                            name: data.name,
                            price: data.price
                          });
                        }
                      }}
                      onVariantAdd={() => {}}
                      onVariantShow={variantId => {
                        if (product) {
                          navigate(
                            productVariantEditUrl(product.id, variantId)
                          );
                        }
                      }}
                      onImageUpload={event => {
                        if (product) {
                          createProductImage({
                            alt: "",
                            image: event.target.files[0],
                            product: product.id
                          });
                        }
                      }}
                    />
                  );
                }}
              </ProductUpdateOperations>
            );
          }}
        </TypedProductDetailsQuery>
      );
    }}
  </Navigator>
);
export default ProductUpdate;
