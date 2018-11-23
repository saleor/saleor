import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductVariant } from "../../types/ProductVariant";
import ProductVariantAttributes from "../ProductVariantAttributes";
import ProductVariantImages from "../ProductVariantImages";
import ProductVariantImageSelectDialog from "../ProductVariantImageSelectDialog";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

interface ProductVariantPageProps {
  variant?: ProductVariant;
  errors: UserError[];
  saveButtonBarState?: SaveButtonBarState;
  loading?: boolean;
  placeholderImage?: string;
  header: string;
  onBack();
  onDelete();
  onSubmit(data: any);
  onImageSelect(id: string);
  onVariantClick(variantId: string);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "4fr 9fr",
    [theme.breakpoints.down("sm")]: {
      gridGap: `${theme.spacing.unit}px`,
      gridTemplateColumns: "1fr"
    }
  }
}));

const ProductVariantPage = decorate<ProductVariantPageProps>(
  ({
    classes,
    errors: formErrors,
    loading,
    header,
    placeholderImage,
    saveButtonBarState,
    variant,
    onBack,
    onDelete,
    onImageSelect,
    onSubmit,
    onVariantClick
  }) => {
    const variantImages = variant ? variant.images.map(image => image.id) : [];
    const productImages = variant
      ? variant.product.images.sort((prev, next) =>
          prev.sortOrder > next.sortOrder ? 1 : -1
        )
      : undefined;
    const images = productImages
      ? productImages
          .filter(image => variantImages.indexOf(image.id) !== -1)
          .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
      : undefined;
    return (
      <Toggle>
        {(isImageSelectModalActive, { toggle: toggleImageSelectModal }) => (
          <>
            <Container width="md">
              <PageHeader title={header} onBack={onBack} />
              <Form
                initial={{
                  attributes:
                    variant && variant.attributes
                      ? variant.attributes.map(a => ({
                          slug: a.attribute.slug,
                          value: a.value.slug
                        }))
                      : [],
                  costPrice:
                    variant && variant.costPrice
                      ? variant.costPrice.amount.toString()
                      : null,
                  priceOverride:
                    variant && variant.priceOverride
                      ? variant.priceOverride.amount.toString()
                      : null,
                  quantity: variant && variant.quantity ? variant.quantity : "",
                  sku: variant && variant.sku
                }}
                errors={formErrors}
                onSubmit={onSubmit}
                key={variant ? JSON.stringify(variant) : "novariant"}
              >
                {({ change, data, errors, hasChanged, submit }) => (
                  <>
                    <div className={classes.root}>
                      <div>
                        <ProductVariantNavigation
                          current={variant ? variant.id : undefined}
                          variants={maybe(() => variant.product.variants)}
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
                            variant && variant.attributes
                              ? variant.attributes.map(a => a.attribute)
                              : undefined
                          }
                          data={data}
                          disabled={loading}
                          onChange={change}
                        />
                        <ProductVariantImages
                          disabled={loading}
                          images={images}
                          placeholderImage={placeholderImage}
                          onImageAdd={toggleImageSelectModal}
                        />
                        <ProductVariantPrice
                          errors={errors}
                          priceOverride={data.priceOverride}
                          currencySymbol={
                            variant && variant.priceOverride
                              ? variant.priceOverride.currency
                              : variant && variant.costPrice
                              ? variant.costPrice.currency
                              : ""
                          }
                          costPrice={data.costPrice}
                          loading={loading}
                          onChange={change}
                        />
                        <ProductVariantStock
                          errors={errors}
                          sku={data.sku}
                          quantity={data.quantity}
                          stockAllocated={
                            variant ? variant.quantityAllocated : undefined
                          }
                          loading={loading}
                          onChange={change}
                        />
                      </div>
                    </div>
                    <SaveButtonBar
                      disabled={loading || !onSubmit || !hasChanged}
                      state={saveButtonBarState}
                      onCancel={onBack}
                      onDelete={onDelete}
                      onSave={submit}
                    />
                  </>
                )}
              </Form>
            </Container>
            {variant && (
              <>
                <ProductVariantImageSelectDialog
                  onClose={toggleImageSelectModal}
                  onImageSelect={onImageSelect}
                  open={isImageSelectModalActive}
                  images={productImages}
                  selectedImages={maybe(() =>
                    variant.images.map(image => image.id)
                  )}
                />
              </>
            )}
          </>
        )}
      </Toggle>
    );
  }
);
ProductVariantPage.displayName = "ProductVariantPage";
export default ProductVariantPage;
