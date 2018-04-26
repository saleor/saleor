import { withStyles } from "material-ui/styles";
import * as React from "react";

import Form from "../../../components/Form";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import ProductAttributesForm from "../ProductAttributesForm";
import ProductAvailabilityForm from "../ProductAvailabilityForm";
import ProductCategoryAndCollectionsForm from "../ProductCategoryAndCollectionsForm";
import ProductDetailsForm from "../ProductDetailsForm";

interface ProductUpdateProps {
  collections?: any[];
  categories?: any[];
  loading?: boolean;
  // TODO: Type it when done
  product?: any;
  onBack();
  onSubmit();
}

const decorate = withStyles(theme => ({
  root: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.up("md")]: {
      marginLeft: "auto",
      marginRight: "auto",
      maxWidth: theme.breakpoints.width("md")
    }
  },
  grid: {
    gridGap: theme.spacing.unit * 2 + "px",
    display: "grid",
    gridTemplateColumns: "3fr 2fr",
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit,
      gridGap: theme.spacing.unit + "px",
      gridTemplateColumns: "1fr"
    }
  },
  cardContainer: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  }
}));
export const ProductUpdate = decorate<ProductUpdateProps>(
  ({
    classes,
    loading,
    categories,
    collections,
    product,
    onBack,
    onSubmit
  }) => {
    const initialData = {
      attributes: loading ? [] : product.attributes,
      available: loading ? "" : product.available,
      availableOn: loading ? "" : product.availableOn,
      category: loading ? "" : product.category.id,
      collections: loading
        ? []
        : product.collections.edges.map(edge => edge.node).map(node => node.id),
      description: loading ? "" : product.description,
      name: loading ? "" : product.name,
      price: loading ? "" : product.price.net,
      seoDescription: loading ? "" : product.seo.description,
      seoTitle: loading ? "" : product.seo.title
    };
    return (
      <div className={classes.root}>
        <Form onSubmit={onSubmit} initial={initialData}>
          {({ change, data, submit }) => (
            <>
              <div className={classes.grid}>
                <div>
                  <ProductDetailsForm
                    onBack={onBack}
                    onChange={change}
                    name={data.name}
                    description={data.description}
                    currencySymbol={loading ? "" : product.price.currencySymbol}
                    price={data.price}
                    loading={loading}
                  />
                  <div className={classes.cardContainer}>
                    <SeoForm
                      title={data.seoTitle}
                      titlePlaceholder={data.name}
                      description={data.seoDescription}
                      descriptionPlaceholder={data.description}
                      storefrontUrl={
                        loading
                          ? ""
                          : `http://demo.getsaleor.com/product/${product.slug}`
                      }
                      loading={loading}
                      onClick={() => {}}
                      onChange={change}
                    />
                  </div>
                </div>
                <div>
                  <ProductAvailabilityForm
                    available={data.available}
                    availableOn={data.availableOn}
                    loading={loading}
                    onChange={change}
                  />
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
                      loading={loading}
                      onChange={change}
                    />
                  </div>
                  <div className={classes.cardContainer}>
                    <ProductAttributesForm
                      attributes={
                        loading
                          ? []
                          : product.productType.productAttributes.edges.map(
                              edge => edge.node
                            )
                      }
                      productAttributes={data.attributes}
                      loading={loading}
                      onChange={change}
                    />
                  </div>
                </div>
              </div>
              <SaveButtonBar
                onSave={submit}
                onBack={onBack}
                disabled={loading}
              />
            </>
          )}
        </Form>
      </div>
    );
  }
);
export default ProductUpdate;
