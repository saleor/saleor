import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import ProductTypeDetails from "../ProductTypeDetails/ProductTypeDetails";
import ProductTypeProperties from "../ProductTypeProperties/ProductTypeProperties";

interface ChoiceType {
  label: string;
  value: string;
}
export interface ProductTypeForm {
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxRate: string;
  productAttributes: ChoiceType[];
  variantAttributes: ChoiceType[];
}
interface ProductTypeDetailsPageProps {
  productType?: {
    id: string;
    name?: string;
    hasVariants?: boolean;
    isShippingRequired?: boolean;
    taxRate?: string;
  };
  productAttributes?: Array<{
    id: string;
    name: string;
  }>;
  variantAttributes?: Array<{
    id: string;
    name: string;
  }>;
  disabled: boolean;
  saveButtonBarState: SaveButtonBarState;
  searchLoading: boolean;
  searchResults: Array<{
    id: string;
    name: string;
  }>;
  taxRates: string[];
  onAttributeSearch: (name: string) => void;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: ProductTypeForm) => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "2fr 1fr"
  }
}));
const ProductTypeDetailsPage = decorate<ProductTypeDetailsPageProps>(
  ({
    classes,
    disabled,
    productType,
    productAttributes,
    variantAttributes,
    saveButtonBarState,
    searchLoading,
    searchResults,
    taxRates,
    onAttributeSearch,
    onBack,
    onDelete,
    onSubmit
  }) => {
    const formInitialData: ProductTypeForm = {
      hasVariants:
        productType && productType.hasVariants !== undefined
          ? productType.hasVariants
          : false,
      isShippingRequired:
        productType && productType.isShippingRequired !== undefined
          ? productType.isShippingRequired
          : false,
      name:
        productType && productType.name !== undefined ? productType.name : "",
      productAttributes:
        productAttributes !== undefined
          ? productAttributes.map(a => ({ label: a.name, value: a.id }))
          : [],
      taxRate: productType && productType.taxRate ? productType.taxRate : null,
      variantAttributes:
        variantAttributes !== undefined
          ? variantAttributes.map(a => ({ label: a.name, value: a.id }))
          : []
    };
    return (
      <Toggle>
        {(openedDeleteDialog, { toggle: toggleDeleteDialog }) => (
          <>
            <Form
              initial={formInitialData}
              onSubmit={onSubmit}
              key={JSON.stringify(productType)}
            >
              {({ change, data, hasChanged, submit }) => (
                <Container width="md">
                  <PageHeader
                    title={productType ? productType.name : undefined}
                    onBack={onBack}
                  />
                  <div className={classes.root}>
                    <div>
                      <ProductTypeDetails
                        data={data}
                        disabled={disabled}
                        searchLoading={searchLoading}
                        searchResults={searchResults
                          .filter(
                            suggestion =>
                              data.productAttributes
                                .map(v => v.value)
                                .indexOf(suggestion.id) === -1
                          )
                          .filter(
                            suggestion =>
                              data.variantAttributes
                                .map(v => v.value)
                                .indexOf(suggestion.id) === -1
                          )}
                        onAttributeSearch={onAttributeSearch}
                        onChange={change}
                      />
                    </div>
                    <div>
                      <ProductTypeProperties
                        data={data}
                        disabled={disabled}
                        taxRates={taxRates}
                        onChange={change}
                      />
                    </div>
                  </div>
                  <SaveButtonBar
                    onCancel={onBack}
                    onDelete={toggleDeleteDialog}
                    onSave={submit}
                    disabled={disabled || !hasChanged}
                    state={saveButtonBarState}
                  />
                </Container>
              )}
            </Form>

            {productType && (
              <ActionDialog
                open={openedDeleteDialog}
                onClose={toggleDeleteDialog}
                onConfirm={onDelete}
                title={i18n.t("Remove product type")}
                variant="delete"
              >
                <DialogContentText
                  dangerouslySetInnerHTML={{
                    __html: i18n.t(
                      "Are you sure you want to remove <strong>{{ name }}</strong>?",
                      { name: productType.name }
                    )
                  }}
                />
              </ActionDialog>
            )}
          </>
        )}
      </Toggle>
    );
  }
);
ProductTypeDetailsPage.displayName = "ProductTypeDetailsPage";
export default ProductTypeDetailsPage;
