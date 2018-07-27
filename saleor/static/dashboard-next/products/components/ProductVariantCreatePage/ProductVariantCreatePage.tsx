import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { AttributeType, ProductImageType } from "../../";
import { UserError } from "../../..";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import ProductVariantAttributes from "../ProductVariantAttributes";
import ProductVariantImages from "../ProductVariantImages";
import ProductVariantImageSelectDialog from "../ProductVariantImageSelectDialog";
import ProductVariantNavigation from "../ProductVariantNavigation";
import ProductVariantPrice from "../ProductVariantPrice";
import ProductVariantStock from "../ProductVariantStock";

interface FormData {
  attributes?: Array<{
    slug: string;
    value: string;
  }>;
  costPrice?: string;
  images?: string[];
  priceOverride?: string;
  stock?: number;
  sku?: string;
}
interface ProductVariantCreatePageProps {
  errors: UserError[];
  header: string;
  loading: boolean;
  product?: {
    images?: {
      edges?: Array<{
        node: ProductImageType;
      }>;
    };
    productType?: {
      name?: string;
      variantAttributes?: {
        edges?: Array<{
          node: AttributeType;
        }>;
      };
    };
    variants?: {
      edges?: Array<{
        node: {
          id: string;
          name: string;
          sku: string;
          images: {
            edges: Array<{
              node: {
                url: string;
              };
            }>;
          };
        };
      }>;
    };
  };
  saveButtonBarState?: SaveButtonBarState;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
  onVariantClick: (variantId: string) => void;
}

const decorate = withStyles(theme => ({
  root: {
    "& input": {
      width: "100%"
    },
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 2.25fr",
    [theme.breakpoints.down("sm")]: {
      gridGap: `${theme.spacing.unit}px`,
      gridTemplateColumns: "1fr"
    }
  }
}));

const ProductVariantCreatePage = decorate<ProductVariantCreatePageProps>(
  ({
    classes,
    errors: formErrors,
    loading,
    header,
    product,
    saveButtonBarState,
    onBack,
    onSubmit,
    onVariantClick
  }) => {
    const handleImageSelect = (ids: string[]) => {};
    return (
      <Toggle>
        {(isImageSelectModalActive, { toggle: toggleImageSelectModal }) => (
          <>
            <Container width="md">
              <PageHeader title={header} onBack={onBack} />
              <Form
                initial={{
                  attributes:
                    product &&
                    product.productType &&
                    product.productType.variantAttributes &&
                    product.productType.variantAttributes.edges
                      ? product.productType.variantAttributes.edges.map(a => ({
                          slug: a.node.slug,
                          value: ""
                        }))
                      : undefined,
                  costPrice: null,
                  images:
                    product && product.images && product.images.edges
                      ? product.images.edges.map(edge => edge.node.id)
                      : undefined,
                  priceOverride: null,
                  sku: null,
                  stock: null
                }}
                errors={formErrors}
                onSubmit={onSubmit}
                key={product ? JSON.stringify(product) : "noproduct"}
              >
                {({ change, data, errors, hasChanged, submit }) => {
                  const images = data.images
                    ? data.images.map(
                        id =>
                          product.images.edges
                            .map(edge => edge.node)
                            .filter(image => image.id === id)[0]
                      )
                    : undefined;
                  return (
                    <>
                      <div className={classes.root}>
                        <div>
                          <ProductVariantNavigation
                            variants={
                              product &&
                              product.variants &&
                              product.variants.edges
                                ? product.variants.edges.map(edge => edge.node)
                                : undefined
                            }
                            onRowClick={(variantId: string) => {
                              if (product && product.variants) {
                                return onVariantClick(variantId);
                              }
                            }}
                          />
                        </div>
                        <div>
                          <ProductVariantAttributes
                            attributes={
                              product &&
                              product.productType &&
                              product.productType.variantAttributes &&
                              product.productType.variantAttributes.edges
                                ? product.productType.variantAttributes.edges.map(
                                    edge => edge.node
                                  )
                                : undefined
                            }
                            data={data}
                            disabled={loading}
                            onChange={change}
                          />
                          {/* TODO: uncomment when API will be ready */}
                          {/* <ProductVariantImages
                            disabled={loading}
                            images={images}
                            placeholderImage={placeholderImage}
                            onImageAdd={toggleImageSelectModal}
                          /> */}
                          <ProductVariantPrice
                            errors={errors}
                            priceOverride={data.priceOverride}
                            // FIXME: currency symbol should be fetched from API
                            currencySymbol="USD"
                            costPrice={data.costPrice}
                            loading={loading}
                            onChange={change}
                          />
                          <ProductVariantStock
                            errors={errors}
                            sku={data.sku}
                            stock={data.stock}
                            loading={loading}
                            onChange={change}
                          />
                        </div>
                      </div>
                      <SaveButtonBar
                        disabled={loading || !onSubmit || !hasChanged}
                        labels={{
                          delete: i18n.t("Remove variant"),
                          save: i18n.t("Save variant")
                        }}
                        state={saveButtonBarState}
                        onCancel={onBack}
                        onSave={submit}
                      />
                    </>
                  );
                }}
              </Form>
            </Container>
            {product && (
              <ProductVariantImageSelectDialog
                onClose={toggleImageSelectModal}
                onConfirm={handleImageSelect}
                open={isImageSelectModalActive}
                images={
                  product.images && product.images.edges
                    ? product.images.edges.map(edge => edge.node)
                    : []
                }
              />
            )}
          </>
        )}
      </Toggle>
    );
  }
);
export default ProductVariantCreatePage;
