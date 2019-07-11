import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import useFormset, {
  FormsetChange,
  FormsetData
} from "@saleor/hooks/useFormset";
import { getAttributeInputFromVariant } from "@saleor/products/utils/data";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { ProductVariant } from "../../types/ProductVariant";
import ProductVariantAttributes, {
  VariantAttributeInputData
} from "../ProductVariantAttributes";
import ProductVariantImages from "../ProductVariantImages";
import ProductVariantImageSelectDialog from "../ProductVariantImageSelectDialog";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

export interface ProductVariantPageFormData {
  costPrice: number;
  priceOverride: number;
  quantity: number;
  sku: string;
}

export interface ProductVariantPageSubmitData
  extends ProductVariantPageFormData {
  attributes: FormsetData<VariantAttributeInputData, string>;
}

interface ProductVariantPageProps {
  variant?: ProductVariant;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  loading?: boolean;
  placeholderImage?: string;
  header: string;
  onAdd();
  onBack();
  onDelete();
  onSubmit(data: ProductVariantPageSubmitData);
  onImageSelect(id: string);
  onVariantClick(variantId: string);
}

const ProductVariantPage: React.FC<ProductVariantPageProps> = ({
  errors: formErrors,
  loading,
  header,
  placeholderImage,
  saveButtonBarState,
  variant,
  onAdd,
  onBack,
  onDelete,
  onImageSelect,
  onSubmit,
  onVariantClick
}) => {
  const attributeInput = React.useMemo(
    () => getAttributeInputFromVariant(variant),
    [variant]
  );
  const { change: changeAttributeData, data: attributes } = useFormset(
    attributeInput
  );

  const [isModalOpened, setModalStatus] = React.useState(false);
  const toggleModal = () => setModalStatus(!isModalOpened);

  const variantImages = maybe(() => variant.images.map(image => image.id), []);
  const productImages = maybe(() =>
    variant.product.images.sort((prev, next) =>
      prev.sortOrder > next.sortOrder ? 1 : -1
    )
  );
  const images = maybe(() =>
    productImages
      .filter(image => variantImages.indexOf(image.id) !== -1)
      .sort((prev, next) => (prev.sortOrder > next.sortOrder ? 1 : -1))
  );

  const initialForm: ProductVariantPageFormData = {
    costPrice: maybe(() => variant.costPrice.amount, 0),
    priceOverride: maybe(() => variant.priceOverride.amount, 0),
    quantity: maybe(() => variant.quantity, 0),
    sku: maybe(() => variant.sku, "")
  };

  const handleSubmit = (data: ProductVariantPageFormData) =>
    onSubmit({
      ...data,
      attributes
    });

  return (
    <>
      <Container>
        <AppHeader onBack={onBack}>
          {maybe(() => variant.product.name)}
        </AppHeader>
        <PageHeader title={header} />
        <Form
          initial={initialForm}
          errors={formErrors}
          onSubmit={handleSubmit}
          confirmLeave
        >
          {({ change, data, errors, hasChanged, submit, triggerChange }) => {
            const handleAttributeChange: FormsetChange = (id, value) => {
              changeAttributeData(id, value);
              triggerChange();
            };

            return (
              <>
                <Grid variant="inverted">
                  <div>
                    <ProductVariantNavigation
                      current={variant ? variant.id : undefined}
                      fallbackThumbnail={maybe(
                        () => variant.product.thumbnail.url
                      )}
                      variants={maybe(() => variant.product.variants)}
                      onAdd={onAdd}
                      onRowClick={(variantId: string) => {
                        if (variant) {
                          return onVariantClick(variantId);
                        }
                      }}
                    />
                  </div>
                  <div>
                    <ProductVariantAttributes
                      attributes={attributes}
                      disabled={loading}
                      onChange={handleAttributeChange}
                    />
                    <CardSpacer />
                    <ProductVariantImages
                      disabled={loading}
                      images={images}
                      placeholderImage={placeholderImage}
                      onImageAdd={toggleModal}
                    />
                    <CardSpacer />
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
                    <CardSpacer />
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
                </Grid>
                <SaveButtonBar
                  disabled={loading || !hasChanged}
                  state={saveButtonBarState}
                  onCancel={onBack}
                  onDelete={onDelete}
                  onSave={submit}
                />
              </>
            );
          }}
        </Form>
      </Container>
      {variant && (
        <ProductVariantImageSelectDialog
          onClose={toggleModal}
          onImageSelect={onImageSelect}
          open={isModalOpened}
          images={productImages}
          selectedImages={maybe(() => variant.images.map(image => image.id))}
        />
      )}
    </>
  );
};
ProductVariantPage.displayName = "ProductVariantPage";
export default ProductVariantPage;
