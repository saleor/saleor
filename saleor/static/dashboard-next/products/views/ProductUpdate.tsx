import * as React from "react";
import { arrayMove } from "react-sortable-hoc";

import { ApolloError } from "apollo-client";
import * as placeholderImg from "../../../images/placeholder255x255.png";
import { attributesListUrl } from "../../attributes";
import { categoryShowUrl } from "../../categories";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
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
  <Messages>
    {pushMessage => {
      return (
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

                  const handleDelete = () => {
                    pushMessage({ text: i18n.t("Product removed") });
                    navigate(categoryShowUrl(data.product.category.id));
                  };
                  const handleError = (error: ApolloError) => {
                    console.error(error.message);
                    pushMessage({ text: i18n.t("Something went wrong") });
                  };
                  const handleUpdate = () =>
                    pushMessage({ text: i18n.t("Saved changes") });
                  const handleImageCreate = () =>
                    pushMessage({
                      text: i18n.t("Image successfully uploaded")
                    });
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
                    <ProductUpdateOperations
                      product={product}
                      onDelete={handleDelete}
                      onError={handleError}
                      onImageCreate={handleImageCreate}
                      onUpdate={handleUpdate}
                    >
                      {({
                        createProductImage,
                        deleteProduct,
                        errors,
                        reorderProductImages,
                        updateProduct
                      }) => {
                        const disableFormSave =
                          createProductImage.loading ||
                          deleteProduct.loading ||
                          reorderProductImages.loading ||
                          updateProduct.loading;
                        const formSubmitState = disableFormSave
                          ? "loading"
                          : "idle";
                        return (
                          <ProductUpdatePage
                            categories={allCategories}
                            collections={allCollections}
                            disabled={disableFormSave}
                            errors={errors}
                            saveButtonBarState={formSubmitState}
                            images={images}
                            placeholderImage={placeholderImg}
                            product={product}
                            productCollections={
                              product && product.collections
                                ? product.collections.edges.map(
                                    edge => edge.node
                                  )
                                : undefined
                            }
                            variants={
                              product && product.variants
                                ? product.variants.edges.map(edge => edge.node)
                                : undefined
                            }
                            onAttributesEdit={() => navigate(attributesListUrl)}
                            onBack={() => {
                              navigate(productListUrl);
                            }}
                            onDelete={deleteProduct.mutate}
                            onProductShow={() => {
                              if (product) {
                                window.open(product.url);
                              }
                            }}
                            onImageReorder={({ newIndex, oldIndex }) => {
                              if (product) {
                                let ids = images.map(image => image.id);
                                ids = arrayMove(ids, oldIndex, newIndex);
                                reorderProductImages.mutate({
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

                                updateProduct.mutate({
                                  attributes,
                                  availableOn:
                                    data.availableOn !== ""
                                      ? data.availableOn
                                      : null,
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
                                createProductImage.mutate({
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
    }}
  </Messages>
);
export default ProductUpdate;
