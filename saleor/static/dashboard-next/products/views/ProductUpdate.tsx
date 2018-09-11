import * as React from "react";
import { arrayMove } from "react-sortable-hoc";

import * as placeholderImg from "../../../images/placeholder255x255.png";
import { attributesListUrl } from "../../attributes";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
import { decimal } from "../../misc";
import ProductUpdatePage from "../components/ProductUpdatePage";
import ProductUpdateOperations from "../containers/ProductUpdateOperations";
import {
  productImageUrl,
  productListUrl,
  productVariantAddUrl,
  productVariantEditUrl
} from "../index";
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
                {({ data, loading, error }) => {
                  if (error) {
                    return <ErrorMessageCard message="Something went wrong" />;
                  }

                  const handleDelete = () => {
                    pushMessage({ text: i18n.t("Product removed") });
                    navigate(productListUrl);
                  };
                  const handleUpdate = () =>
                    pushMessage({ text: i18n.t("Saved changes") });
                  const handleImageCreate = () =>
                    pushMessage({
                      text: i18n.t("Image successfully uploaded")
                    });
                  const handleImageDeleteSuccess = () =>
                    pushMessage({
                      text: i18n.t("Image successfully deleted")
                    });
                  const handleVariantAdd = () =>
                    navigate(productVariantAddUrl(id));

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
                      onImageCreate={handleImageCreate}
                      onImageDelete={handleImageDeleteSuccess}
                      onUpdate={handleUpdate}
                    >
                      {({
                        createProductImage,
                        deleteProduct,
                        deleteProductImage,
                        errors,
                        reorderProductImages,
                        updateProduct
                      }) => {
                        const handleImageDelete = (id: string) => () =>
                          deleteProductImage.mutate({ id });
                        const handleImageEdit = (imageId: string) => () =>
                          navigate(productImageUrl(id, imageId));
                        const handleSubmit = data => {
                          if (product) {
                            updateProduct.mutate({
                              attributes: data.attributes,
                              availableOn:
                                data.availableOn !== ""
                                  ? data.availableOn
                                  : null,
                              category: data.category,
                              chargeTaxes: data.chargeTaxes,
                              collections: data.collections,
                              description: data.description,
                              id: product.id,
                              isPublished: data.available,
                              name: data.name,
                              price: decimal(data.price)
                            });
                          }
                        };

                        const disableFormSave =
                          createProductImage.loading ||
                          deleteProduct.loading ||
                          reorderProductImages.loading ||
                          updateProduct.loading ||
                          loading;
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
                            header={product ? product.name : undefined}
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
                            onDelete={() => deleteProduct.mutate({ id })}
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
                            onSubmit={handleSubmit}
                            onVariantAdd={handleVariantAdd}
                            onVariantShow={variantId => () =>
                              navigate(
                                productVariantEditUrl(product.id, variantId)
                              )}
                            onImageUpload={event => {
                              if (product) {
                                createProductImage.mutate({
                                  alt: "",
                                  image: event.target.files[0],
                                  product: product.id
                                });
                              }
                            }}
                            onImageEdit={handleImageEdit}
                            onImageDelete={handleImageDelete}
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
