import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import * as CRC from "crc-32";
import * as React from "react";

import {
  AttributeType,
  AttributeValueType,
  MoneyType,
  ProductImageType
} from "../../";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import ProductVariantAttributes from "../ProductVariantAttributes";
import ProductVariantDeleteDialog from "../ProductVariantDeleteDialog";
import ProductVariantImages from "../ProductVariantImages";
import ProductVariantImageSelectDialog from "../ProductVariantImageSelectDialog";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantProduct from "../ProductVariantProduct";
import ProductVariantStock from "../ProductVariantStock";

interface ProductVariantPageProps {
  variant?: {
    id: string;
    attributes: Array<{
      attribute: AttributeType;
      value: AttributeValueType;
    }>;
    costPrice?: MoneyType;
    images: {
      edges: Array<{
        node: {
          id: string;
        };
      }>;
    };
    name: string;
    priceOverride?: MoneyType;
    product: {
      id: string;
      images: {
        edges: Array<{
          node: ProductImageType;
        }>;
      };
      name: string;
      thumbnailUrl: string;
      variants: {
        edges: Array<{
          node: {
            id: string;
            name: string;
          };
        }>;
        totalCount: number;
      };
    };
    sku: string;
    quantity: number;
    quantityAllocated: number;
  };
  saveButtonBarState?: SaveButtonBarState;
  loading?: boolean;
  placeholderImage?: string;
  onBack();
  onDelete();
  onSubmit(data: any);
  onImageSelect(images: string[]);
  onVariantClick(variantId: string);
}

const decorate = withStyles(theme => ({
  root: {
    "& input": {
      width: "100%"
    },
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 2fr",
    [theme.breakpoints.down("sm")]: {
      gridGap: `${theme.spacing.unit}px`,
      gridTemplateColumns: "1fr"
    }
  }
}));

const ProductVariantPage = decorate<ProductVariantPageProps>(
  ({
    classes,
    variant,
    loading,
    placeholderImage,
    onBack,
    onDelete,
    saveButtonBarState,
    onSubmit,
    onImageSelect,
    onVariantClick
  }) => {
    const attributes = variant
      ? variant.attributes.reduce((prev, curr) => {
          prev[curr.attribute.slug] = curr.value.slug;
          return prev;
        }, {})
      : {};
    const variantImages = variant
      ? variant.images.edges.map(edge => edge.node.id)
      : [];
    const productImages = variant
      ? variant.product.images.edges
          .map(edge => edge.node)
          .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
      : undefined;
    const images = productImages
      ? productImages
          .filter(image => variantImages.indexOf(image.id) !== -1)
          .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
      : undefined;
    const handleImageSelect = (images: string[]) => {};
    return (
      <Toggle>
        {(isModalActive, { toggle: toggleDeleteModal }) => (
          <Toggle>
            {(isImageSelectModalActive, { toggle: toggleImageSelectModal }) => (
              <>
                <Container width="md">
                  <PageHeader
                    title={variant ? variant.name : undefined}
                    onBack={onBack}
                  >
                    <IconButton onClick={toggleDeleteModal} disabled={loading}>
                      <DeleteIcon />
                    </IconButton>
                  </PageHeader>
                  <Form
                    initial={{
                      costPrice:
                        variant && variant.costPrice
                          ? variant.costPrice.amount.toString()
                          : null,
                      priceOverride:
                        variant && variant.priceOverride
                          ? variant.priceOverride.amount.toString()
                          : null,
                      sku: variant && variant.sku,
                      stock:
                        variant && variant.quantity ? variant.quantity : "",
                      ...attributes
                    }}
                    onSubmit={onSubmit}
                    key={variant ? CRC.str(JSON.stringify(variant)) : "loading"}
                  >
                    {({ change, data, hasChanged, submit }) => (
                      <>
                        <div className={classes.root}>
                          <div>
                            <ProductVariantProduct
                              product={variant ? variant.product : undefined}
                              loading={loading}
                              placeholderImage={placeholderImage}
                            />
                            <ProductVariantNavigation
                              current={variant ? variant.id : undefined}
                              loading={loading}
                              productId={
                                variant ? variant.product.id : undefined
                              }
                              variants={
                                variant
                                  ? variant.product.variants.edges.map(
                                      edge => edge.node
                                    )
                                  : undefined
                              }
                              onRowClick={(variantId: string) => {
                                if (variant) {
                                  return onVariantClick(variantId);
                                }
                              }}
                            />
                          </div>
                          <div>
                            <ProductVariantAttributes
                              attributes={
                                variant ? variant.attributes : undefined
                              }
                              data={data}
                              onChange={change}
                              loading={loading}
                            />
                            <ProductVariantPrice
                              priceOverride={data.priceOverride}
                              currencySymbol={
                                variant && variant.priceOverride
                                  ? variant.priceOverride.currency
                                  : ""
                              }
                              costPrice={data.costPrice}
                              loading={loading}
                              onChange={change}
                            />
                            <ProductVariantStock
                              sku={data.sku}
                              stock={data.stock}
                              stockAllocated={
                                variant ? variant.quantityAllocated : undefined
                              }
                              loading={loading}
                              onChange={change}
                            />
                            <ProductVariantImages
                              images={images}
                              placeholderImage={placeholderImage}
                              onImageAdd={toggleImageSelectModal}
                              loading={loading}
                            />
                          </div>
                        </div>
                        <SaveButtonBar
                          disabled={loading || !onSubmit || !hasChanged}
                          state={saveButtonBarState}
                          onSave={submit}
                        />
                      </>
                    )}
                  </Form>
                </Container>
                {variant && (
                  <>
                    <ProductVariantDeleteDialog
                      onClose={toggleDeleteModal}
                      onConfirm={onDelete}
                      open={isModalActive}
                      name={variant.name}
                    />
                    <ProductVariantImageSelectDialog
                      onClose={toggleImageSelectModal}
                      onConfirm={handleImageSelect}
                      open={isImageSelectModalActive}
                      images={productImages}
                    />
                  </>
                )}
              </>
            )}
          </Toggle>
        )}
      </Toggle>
    );
  }
);
export default ProductVariantPage;
