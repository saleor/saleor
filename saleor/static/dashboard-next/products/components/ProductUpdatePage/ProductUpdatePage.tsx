import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import {
  ProductDetails_product,
  ProductDetails_product_images,
  ProductDetails_product_variants_priceOverride
} from "../../types/ProductDetails";
import ProductAvailabilityForm from "../ProductAvailabilityForm";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductImages from "../ProductImages";
import ProductOrganization from "../ProductOrganization";
import ProductPricing from "../ProductPricing";
import ProductStock from "../ProductStock";
import ProductVariants from "../ProductVariants";

interface ProductUpdateProps {
  errors: UserError[];
  placeholderImage: string;
  collections?: Array<{
    id: string;
    name: string;
  }>;
  categories?: Array<{
    id: string;
    name: string;
  }>;
  disabled?: boolean;
  productCollections?: Array<{
    id: string;
    name: string;
  }>;
  variants?: Array<{
    id: string;
    sku: string;
    name: string;
    priceOverride?: ProductDetails_product_variants_priceOverride;
    stockQuantity: number;
    margin: number;
  }>;
  images?: ProductDetails_product_images[];
  product?: ProductDetails_product;
  header: string;
  saveButtonBarState: ConfirmButtonTransitionState;
  onVariantShow: (id: string) => () => void;
  onImageDelete: (id: string) => () => void;
  onAttributesEdit: () => void;
  onBack?();
  onDelete();
  onImageEdit?(id: string);
  onImageReorder?(event: { oldIndex: number; newIndex: number });
  onImageUpload?(event: React.ChangeEvent<any>);
  onProductShow?();
  onSeoClick?();
  onSubmit?(data: any);
  onVariantAdd?();
}

const decorate = withStyles(theme => ({
  cardContainer: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  root: {
    display: "grid",
    gridGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr",
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      gridGap: theme.spacing.unit + "px",
      gridTemplateColumns: "1fr",
      marginTop: theme.spacing.unit
    }
  }
}));

export const ProductUpdate = decorate<ProductUpdateProps>(
  ({
    classes,
    disabled,
    categories: categoryChoiceList,
    collections: collectionChoiceList,
    errors: userErrors,
    images,
    header,
    placeholderImage,
    product,
    productCollections,
    saveButtonBarState,
    variants,
    onAttributesEdit,
    onBack,
    onDelete,
    onImageDelete,
    onImageEdit,
    onImageReorder,
    onImageUpload,
    onSeoClick,
    onSubmit,
    onVariantAdd,
    onVariantShow
  }) => {
    const initialData = product
      ? {
          attributes: product.attributes
            ? product.attributes.map(a => ({
                slug: a.attribute.slug,
                value: a.value ? a.value.slug : null
              }))
            : undefined,
          available: product.isPublished,
          availableOn: product.availableOn,
          category: product.category ? product.category.id : undefined,
          chargeTaxes: product.chargeTaxes ? product.chargeTaxes : false,
          collections: productCollections
            ? productCollections.map(node => node.id)
            : [],
          description: product.description,
          name: product.name,
          price: product.price ? product.price.amount.toString() : undefined,
          productType:
            product.productType && product.attributes
              ? {
                  label: product.productType.name,
                  value: {
                    hasVariants: product.productType.hasVariants,
                    id: product.productType.id,
                    name: product.productType.name,
                    productAttributes: product.attributes.map(a => a.attribute)
                  }
                }
              : undefined,
          seoDescription: product.seoDescription,
          seoTitle: product.seoTitle,
          sku:
            product.productType && product.productType.hasVariants
              ? undefined
              : variants && variants[0]
              ? variants[0].sku
              : undefined,
          stockQuantity:
            product.productType && product.productType.hasVariants
              ? undefined
              : variants && variants[0]
              ? variants[0].stockQuantity
              : undefined
        }
      : {
          availableOn: "",
          chargeTaxes: false,
          collections: [],
          description: "",
          featured: false,
          name: "",
          seoDescription: "",
          seoTitle: ""
        };
    const categories =
      categoryChoiceList !== undefined
        ? categoryChoiceList.map(category => ({
            label: category.name,
            value: category.id
          }))
        : [];
    const collections =
      collectionChoiceList !== undefined
        ? collectionChoiceList.map(collection => ({
            label: collection.name,
            value: collection.id
          }))
        : [];
    const currency =
      product && product.price ? product.price.currency : undefined;
    const hasVariants =
      product && product.productType && product.productType.hasVariants;

    return (
      <Form
        onSubmit={onSubmit}
        errors={userErrors}
        initial={initialData}
        key={product ? JSON.stringify(product) : "loading"}
      >
        {({ change, data, errors, hasChanged, submit }) => (
          <>
            <Container width="md">
              <PageHeader title={header} onBack={onBack} />
              <div className={classes.root}>
                <div>
                  <ProductDetailsForm
                    data={data}
                    disabled={disabled}
                    errors={errors}
                    onChange={change}
                  />
                  <div className={classes.cardContainer}>
                    <ProductImages
                      images={images}
                      placeholderImage={placeholderImage}
                      onImageDelete={onImageDelete}
                      onImageReorder={onImageReorder}
                      onImageEdit={onImageEdit}
                      onImageUpload={onImageUpload}
                    />
                  </div>
                  <div className={classes.cardContainer}>
                    <ProductPricing
                      currency={currency}
                      data={data}
                      disabled={disabled}
                      onChange={change}
                    />
                  </div>
                  <div className={classes.cardContainer}>
                    {hasVariants ? (
                      <ProductVariants
                        variants={variants}
                        fallbackPrice={product ? product.price : undefined}
                        onAttributesEdit={onAttributesEdit}
                        onRowClick={onVariantShow}
                        onVariantAdd={onVariantAdd}
                      />
                    ) : (
                      <ProductStock
                        data={data}
                        disabled={disabled}
                        onChange={change}
                      />
                    )}
                  </div>
                  <div className={classes.cardContainer}>
                    <SeoForm
                      helperText={i18n.t(
                        "Add search engine title and description to make this product easier to find"
                      )}
                      title={data.seoTitle}
                      titlePlaceholder={data.name}
                      description={data.seoDescription}
                      descriptionPlaceholder={data.description}
                      loading={disabled}
                      onClick={onSeoClick}
                      onChange={change}
                    />
                  </div>
                </div>
                <div>
                  <ProductOrganization
                    category={data.category}
                    categories={categories}
                    errors={errors}
                    productCollections={data.collections}
                    collections={collections}
                    product={product}
                    data={data}
                    disabled={disabled}
                    onChange={change}
                  />
                  <div className={classes.cardContainer}>
                    <ProductAvailabilityForm
                      data={data}
                      errors={errors}
                      loading={disabled}
                      onChange={change}
                    />
                  </div>
                </div>
              </div>
              <SaveButtonBar
                onCancel={onBack}
                onDelete={onDelete}
                onSave={submit}
                state={saveButtonBarState}
                disabled={disabled || !hasChanged}
              />
            </Container>
          </>
        )}
      </Form>
    );
  }
);
ProductUpdate.displayName = "ProductUpdate";
export default ProductUpdate;
