import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
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
      attribute: {
        name: string;
        slug: string;
        values: string[];
      };
      value: string;
    }>;
    images: {
      edges: Array<{
        node: {
          id: string;
        };
      }>;
    };
    name: string;
    priceOverride: {
      currency: string;
      amount: number;
    };
    product: {
      id: string;
      name: string;
      thumbnailUrl: string;
      variants: {
        totalCount: number;
        edges: Array<{
          node: {
            id: string;
            name: string;
          };
        }>;
      };
      images: {
        edges: Array<{
          node: {
            id: string;
            url: string;
            alt: string;
            order: number;
          };
        }>;
      };
    };
    sku: string;
    stock: number;
    stockAllocated: number;
  };
  loading?: boolean;
  placeholderImage?: string;
  onBack();
  onDelete();
  onImageSelect(images: string[]);
}

const decorate = withStyles(theme => ({
  root: {
    gridGap: `${theme.spacing.unit * 2}px`,
    display: "grid",
    gridTemplateColumns: "1fr 2fr",
    [theme.breakpoints.down("sm")]: {
      gridGap: `${theme.spacing.unit}px`,
      gridTemplateColumns: "1fr"
    },
    "& input": {
      width: "100%"
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
    onImageSelect
  }) => {
    const attributes = loading
      ? {}
      : variant.attributes.reduce((prev, curr) => {
          prev[curr.attribute.slug] = curr.value;
          return prev;
        }, {});
    const variantImages = loading
      ? undefined
      : variant.images.edges.map(edge => edge.node.id);
    const productImages = loading
      ? undefined
      : variant.product.images.edges
          .map(edge => edge.node)
          .sort((prev, next) => (prev.order > next.order ? 1 : -1));
    const images = loading
      ? undefined
      : productImages
          .filter(image => variantImages.indexOf(image.id) !== -1)
          .sort((prev, next) => (prev.order > next.order ? 1 : -1));
    const handleImageSelect = (images: string[]) => {};
    return (
      <Toggle>
        {(isModalActive, { toggle: toggleDeleteModal }) => (
          <Toggle>
            {(isImageSelectModalActive, { toggle: toggleImageSelectModal }) => (
              <>
                <Container width="md">
                  <PageHeader
                    title={loading ? undefined : variant.name}
                    onBack={onBack}
                  >
                    <IconButton onClick={toggleDeleteModal} disabled={loading}>
                      <DeleteIcon />
                    </IconButton>
                  </PageHeader>
                  <Form
                    initial={{
                      costPrice: loading
                        ? undefined
                        : variant.priceOverride.amount,
                      priceOverride: loading
                        ? undefined
                        : variant.priceOverride.amount,
                      stock: loading ? undefined : variant.stock,
                      sku: loading ? undefined : variant.sku,
                      ...attributes
                    }}
                  >
                    {({ change, data, submit }) => (
                      <>
                        <div className={classes.root}>
                          <div>
                            <ProductVariantProduct
                              product={loading ? undefined : variant.product}
                              loading={loading}
                              placeholderImage={placeholderImage}
                            />
                            <ProductVariantNavigation
                              variants={
                                loading
                                  ? undefined
                                  : variant.product.variants.edges.map(
                                      edge => edge.node
                                    )
                              }
                              current={loading ? undefined : variant.id}
                              loading={loading}
                              onRowClick={(id: string) => () => {}}
                            />
                          </div>
                          <div>
                            <ProductVariantAttributes
                              attributes={
                                loading ? undefined : variant.attributes
                              }
                              formData={data}
                              onChange={change}
                              loading={loading}
                            />
                            <ProductVariantPrice
                              priceOverride={data.priceOverride}
                              currencySymbol={
                                loading ? "" : variant.priceOverride.currency
                              }
                              costPrice={data.costPrice}
                              loading={loading}
                              onChange={change}
                            />
                            <ProductVariantStock
                              sku={data.sku}
                              stock={data.stock}
                              stockAllocated={
                                loading ? undefined : variant.stockAllocated
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
                          disabled={loading}
                          state={loading ? "disabled" : "default"}
                          onSave={submit}
                        />
                      </>
                    )}
                  </Form>
                </Container>
                {!loading && (
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
