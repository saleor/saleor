import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import VisibilityIcon from "@material-ui/icons/Visibility";
import * as React from "react";

import DialogContentText from "@material-ui/core/DialogContentText";
import { AttributeType } from "../../";
import ActionDialog from "../../../components/ActionDialog";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import ProductAttributesForm from "../ProductAttributesForm";
import ProductAvailabilityForm from "../ProductAvailabilityForm";
import ProductCategoryAndCollectionsForm from "../ProductCategoryAndCollectionsForm";
import ProductDetailsForm from "../ProductDetailsForm";
import ProductImages from "../ProductImages";
import ProductPrice from "../ProductPrice/ProductPrice";
import ProductVariants from "../ProductVariants";

interface MoneyType {
  currency: string;
  amount: number;
}
interface ProductUpdateProps {
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
    priceOverride: number;
    quantity: number;
    margin: number;
  }>;
  images?: Array<{
    id: string;
    alt?: string;
    image: string;
    sortOrder: number;
  }>;
  product?: {
    id: string;
    seoTitle: string;
    seoDescription: string;
    productType: {
      id: string;
    };
    name: string;
    description: string;
    category: {
      id: string;
      name: string;
    };
    price: MoneyType;
    availableOn: string;
    isPublished: boolean;
    attributes: Array<{
      attribute: AttributeType & {
        values: AttributeType[];
      };
      value: AttributeType;
    }>;
    availability: {
      available: boolean;
    };
    purchaseCost: {
      start: MoneyType;
      stop: MoneyType;
    };
    margin: {
      start: number;
      stop: number;
    };
  };
  storefrontUrl?(value: string): string;
  onBack?();
  onDelete?();
  onImageEdit?(id: string);
  onImageReorder?();
  onImageUpload?(event: React.ChangeEvent<any>);
  onProductShow?();
  onSeoClick?();
  onSubmit?();
  onVariantAdd?();
  onVariantShow?(id: string);
}

const shallowCompare = (a, b) => {
  let ret = true;
  Object.keys(a).forEach(k => {
    if (a[k] !== b[k]) {
      ret = false;
    }
  });
  return ret;
};

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
    gridTemplateColumns: "3fr 2fr",
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
    categories,
    collections,
    images,
    placeholderImage,
    product,
    productCollections,
    storefrontUrl,
    variants,
    onBack,
    onDelete,
    onImageEdit,
    onImageReorder,
    onImageUpload,
    onProductShow,
    onSeoClick,
    onSubmit,
    onVariantAdd,
    onVariantShow
  }) => {
    const initialData = {
      available:
        product && product.availability
          ? product.availability.available
          : false,
      availableOn: product ? product.availableOn : "",
      category: product && product.category ? product.category.id : undefined,
      collections:
        product && productCollections
          ? productCollections.map(node => node.id)
          : [],
      description: product ? product.description : "",
      name: product ? product.name : "",
      price: product && product.price ? product.price.amount : undefined,
      seoDescription: product ? product.seoDescription : "",
      seoTitle: product ? product.seoTitle : ""
    };
    if (product && product.attributes) {
      product.attributes.forEach(attr => {
        initialData[attr.attribute.slug] = attr.value.slug;
      });
    }
    return (
      <Form
        onSubmit={onSubmit}
        initial={initialData}
        key={product && product.name ? product.name : "loading"}
      >
        {({ change, data, submit }) => (
          <Container width="md">
            <Toggle>
              {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
                <>
                  <PageHeader
                    title={product ? product.name : undefined}
                    onBack={onBack}
                  >
                    {!!onProductShow && (
                      <IconButton onClick={onProductShow} disabled={disabled}>
                        <VisibilityIcon />
                      </IconButton>
                    )}
                    {!!onDelete && (
                      <IconButton
                        onClick={toggleDeleteDialog}
                        disabled={disabled}
                      >
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </PageHeader>
                  {product &&
                    product.name && (
                      <ActionDialog
                        open={openedDeleteDialog}
                        onClose={toggleDeleteDialog}
                        onConfirm={onDelete}
                        variant="delete"
                        title={i18n.t("Remove product")}
                      >
                        <DialogContentText
                          dangerouslySetInnerHTML={{
                            __html: i18n.t(
                              "Are you sure you want to remove <strong>{{ name }}</strong>?",
                              { name: product.name }
                            )
                          }}
                        />
                      </ActionDialog>
                    )}
                </>
              )}
            </Toggle>
            <div className={classes.root}>
              <div>
                <ProductDetailsForm
                  onBack={onBack}
                  onChange={change}
                  name={data.name}
                  description={data.description}
                  currencySymbol={
                    product && product.price ? product.price.currency : ""
                  }
                  price={data.price}
                  disabled={disabled}
                />
                <div className={classes.cardContainer}>
                  <ProductImages
                    images={images}
                    placeholderImage={placeholderImage}
                    onImageReorder={onImageReorder}
                    onImageEdit={onImageEdit}
                    onImageUpload={onImageUpload}
                  />
                </div>
                <div className={classes.cardContainer}>
                  <ProductVariants
                    variants={variants}
                    fallbackPrice={product ? product.price : undefined}
                    onRowClick={onVariantShow}
                    onVariantAdd={onVariantAdd}
                  />
                </div>
                <div className={classes.cardContainer}>
                  <SeoForm
                    title={data.seoTitle}
                    titlePlaceholder={data.name}
                    description={data.seoDescription}
                    descriptionPlaceholder={data.description}
                    storefrontUrl={storefrontUrl}
                    loading={disabled}
                    onClick={onSeoClick}
                    onChange={change}
                  />
                </div>
              </div>
              <div>
                <ProductAvailabilityForm
                  available={data.available}
                  availableOn={data.availableOn}
                  loading={disabled}
                  onChange={change}
                />
                <div className={classes.cardContainer}>
                  <ProductPrice
                    margin={
                      product && product.margin ? product.margin : undefined
                    }
                    purchaseCost={
                      product && product.purchaseCost
                        ? product.purchaseCost
                        : undefined
                    }
                  />
                </div>
                <div className={classes.cardContainer}>
                  <ProductCategoryAndCollectionsForm
                    category={data.category}
                    categories={
                      categories !== undefined && categories !== null
                        ? categories.map(category => ({
                            label: category.name,
                            value: category.id
                          }))
                        : []
                    }
                    productCollections={data.collections}
                    collections={
                      collections !== undefined && collections !== null
                        ? collections.map(collection => ({
                            label: collection.name,
                            value: collection.id
                          }))
                        : []
                    }
                    loading={disabled}
                    onChange={change}
                  />
                </div>
                <div className={classes.cardContainer}>
                  <ProductAttributesForm
                    attributes={product ? product.attributes : undefined}
                    data={data}
                    disabled={disabled}
                    onChange={change}
                  />
                </div>
              </div>
            </div>
            <SaveButtonBar
              onSave={submit}
              state={"default"}
              disabled={
                disabled || !onSubmit || shallowCompare(initialData, data)
              }
            />
          </Container>
        )}
      </Form>
    );
  }
);
export default ProductUpdate;
