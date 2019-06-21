import Button from "@material-ui/core/Button";
import React from "react";

import { attributeUrl } from "@saleor/attributes/urls";
import AssignAttributeDialog from "@saleor/components/AssignAttributeDialog";
import { WindowTitle } from "@saleor/components/WindowTitle";
import { DEFAULT_INITIAL_SEARCH_DATA } from "@saleor/config";
import SearchAttributes from "@saleor/containers/SearchAttributes";
import useBulkActions from "@saleor/hooks/useBulkActions";
import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "@saleor/i18n";
import { getMutationState, maybe, stopPropagation } from "@saleor/misc";
import ProductTypeAttributeUnassignDialog from "@saleor/productTypes/components/ProductTypeAttributeUnassignDialog";
import ProductTypeBulkAttributeUnassignDialog from "@saleor/productTypes/components/ProductTypeBulkAttributeUnassignDialog";
import ProductTypeDeleteDialog from "@saleor/productTypes/components/ProductTypeDeleteDialog";
import { AssignAttribute } from "@saleor/productTypes/types/AssignAttribute";
import { UnassignAttribute } from "@saleor/productTypes/types/UnassignAttribute";
import { AttributeTypeEnum } from "@saleor/types/globalTypes";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../../components/ProductTypeDetailsPage";
import ProductTypeOperations from "../../containers/ProductTypeOperations";
import { TypedProductTypeDetailsQuery } from "../../queries";
import { ProductTypeDelete } from "../../types/ProductTypeDelete";
import { ProductTypeUpdate as ProductTypeUpdateMutation } from "../../types/ProductTypeUpdate";
import {
  productTypeListUrl,
  productTypeUrl,
  ProductTypeUrlQueryParams
} from "../../urls";
import { ProductTypeUpdateErrors } from "./errors";

interface ProductTypeUpdateProps {
  id: string;
  params: ProductTypeUrlQueryParams;
}

export const ProductTypeUpdate: React.FC<ProductTypeUpdateProps> = ({
  id,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const productAttributeListActions = useBulkActions();
  const variantAttributeListActions = useBulkActions();

  return (
    <ProductTypeUpdateErrors>
      {({ errors, set: setErrors }) => (
        <TypedProductTypeDetailsQuery
          displayLoader
          variables={{ id }}
          require={["productType"]}
        >
          {({ data, loading: dataLoading }) => {
            const closeModal = () => navigate(productTypeUrl(id), true);

            const handleAttributeAssignSuccess = (data: AssignAttribute) => {
              if (data.attributeAssign.errors.length === 0) {
                notify({
                  text: i18n.t("Attributes assigned", {
                    context: "notification"
                  })
                });
                closeModal();
              } else if (
                data.attributeAssign.errors !== null &&
                data.attributeAssign.errors.length > 0
              ) {
                setErrors.addAttributeErrors(data.attributeAssign.errors);
              }
            };
            const handleAttributeUnassignSuccess = (
              data: UnassignAttribute
            ) => {
              if (!data.attributeUnassign.errors) {
                notify({
                  text: i18n.t("Attribute unassigned", {
                    context: "notification"
                  })
                });
              }
            };
            const handleProductTypeDeleteSuccess = (
              deleteData: ProductTypeDelete
            ) => {
              if (deleteData.productTypeDelete.errors.length === 0) {
                notify({
                  text: i18n.t("Product type deleted", {
                    context: "notification"
                  })
                });
                navigate(productTypeListUrl(), true);
              }
            };
            const handleProductTypeUpdateSuccess = (
              updateData: ProductTypeUpdateMutation
            ) => {
              if (
                !updateData.productTypeUpdate.errors ||
                updateData.productTypeUpdate.errors.length === 0
              ) {
                notify({
                  text: i18n.t("Product type updated", {
                    context: "notification"
                  })
                });
              } else if (
                updateData.productTypeUpdate.errors !== null &&
                updateData.productTypeUpdate.errors.length > 0
              ) {
                setErrors.formErrors(updateData.productTypeUpdate.errors);
              }
            };

            return (
              <ProductTypeOperations
                onAssignAttribute={handleAttributeAssignSuccess}
                onUnassignAttribute={handleAttributeUnassignSuccess}
                onProductTypeDelete={handleProductTypeDeleteSuccess}
                onProductTypeUpdate={handleProductTypeUpdateSuccess}
              >
                {({
                  assignAttribute,
                  deleteProductType,
                  unassignAttribute,
                  updateProductType
                }) => {
                  const handleProductTypeDelete = () =>
                    deleteProductType.mutate({ id });
                  const handleProductTypeUpdate = (
                    formData: ProductTypeForm
                  ) => {
                    updateProductType.mutate({
                      id,
                      input: {
                        hasVariants: formData.hasVariants,
                        isShippingRequired: formData.isShippingRequired,
                        name: formData.name,
                        productAttributes: formData.productAttributes.map(
                          choice => choice.value
                        ),
                        taxCode: formData.taxType.value,
                        variantAttributes: formData.variantAttributes.map(
                          choice => choice.value
                        ),
                        weight: formData.weight
                      }
                    });
                  };
                  const handleAssignAttribute = () =>
                    assignAttribute.mutate({
                      id,
                      operations: params.ids.map(id => ({
                        attributeId: id,
                        attributeType: AttributeTypeEnum[params.type]
                      }))
                    });

                  const handleAttributeUnassign = () =>
                    unassignAttribute.mutate({
                      id,
                      ids: [params.id]
                    });

                  const handleBulkAttributeUnassign = () =>
                    unassignAttribute.mutate({
                      id,
                      ids: params.ids
                    });

                  const loading = updateProductType.opts.loading || dataLoading;

                  const assignTransactionState = getMutationState(
                    assignAttribute.opts.called,
                    assignAttribute.opts.loading,
                    maybe(
                      () => assignAttribute.opts.data.attributeAssign.errors
                    )
                  );

                  const unassignTransactionState = getMutationState(
                    unassignAttribute.opts.called,
                    unassignAttribute.opts.loading,
                    maybe(
                      () => unassignAttribute.opts.data.attributeUnassign.errors
                    )
                  );

                  const deleteTransactionState = getMutationState(
                    deleteProductType.opts.called,
                    deleteProductType.opts.loading,
                    maybe(
                      () => deleteProductType.opts.data.productTypeDelete.errors
                    )
                  );

                  const formTransitionState = getMutationState(
                    updateProductType.opts.called,
                    updateProductType.opts.loading,
                    maybe(
                      () => updateProductType.opts.data.productTypeUpdate.errors
                    )
                  );

                  return (
                    <>
                      <WindowTitle title={maybe(() => data.productType.name)} />
                      <ProductTypeDetailsPage
                        defaultWeightUnit={maybe(
                          () => data.shop.defaultWeightUnit
                        )}
                        disabled={loading}
                        errors={errors.formErrors}
                        pageTitle={maybe(() => data.productType.name)}
                        productType={maybe(() => data.productType)}
                        saveButtonBarState={formTransitionState}
                        taxTypes={maybe(() => data.taxTypes, [])}
                        onAttributeAdd={type =>
                          navigate(
                            productTypeUrl(id, {
                              action: "assign-attribute",
                              type
                            })
                          )
                        }
                        onAttributeClick={attributeId =>
                          navigate(attributeUrl(attributeId))
                        }
                        onAttributeUnassign={attributeId =>
                          navigate(
                            productTypeUrl(id, {
                              action: "unassign-attribute",
                              id: attributeId
                            })
                          )
                        }
                        onBack={() => navigate(productTypeListUrl())}
                        onDelete={() =>
                          navigate(
                            productTypeUrl(id, {
                              action: "remove"
                            })
                          )
                        }
                        onSubmit={handleProductTypeUpdate}
                        productAttributeList={{
                          isChecked: productAttributeListActions.isSelected,
                          selected:
                            productAttributeListActions.listElements.length,
                          toggle: productAttributeListActions.toggle,
                          toggleAll: productAttributeListActions.toggleAll,
                          toolbar: (
                            <Button
                              color="primary"
                              onClick={() =>
                                navigate(
                                  productTypeUrl(id, {
                                    action: "unassign-attributes",
                                    ids:
                                      productAttributeListActions.listElements
                                  })
                                )
                              }
                            >
                              {i18n.t("Unassign", {
                                context: "unassign attribute from product type"
                              })}
                            </Button>
                          )
                        }}
                        variantAttributeList={{
                          isChecked: variantAttributeListActions.isSelected,
                          selected:
                            variantAttributeListActions.listElements.length,
                          toggle: variantAttributeListActions.toggle,
                          toggleAll: variantAttributeListActions.toggleAll,
                          toolbar: (
                            <Button
                              color="primary"
                              onClick={() =>
                                navigate(
                                  productTypeUrl(id, {
                                    action: "unassign-attributes",
                                    ids:
                                      variantAttributeListActions.listElements
                                  })
                                )
                              }
                            >
                              {i18n.t("Unassign", {
                                context: "unassign attribute from product type"
                              })}
                            </Button>
                          )
                        }}
                      />
                      {!dataLoading && (
                        <SearchAttributes
                          variables={DEFAULT_INITIAL_SEARCH_DATA}
                        >
                          {({ search, result }) => (
                            <>
                              {Object.keys(AttributeTypeEnum).map(key => (
                                <AssignAttributeDialog
                                  attributes={maybe(() =>
                                    result.data.attributes.edges.map(
                                      edge => edge.node
                                    )
                                  )}
                                  confirmButtonState={assignTransactionState}
                                  loading={result.loading}
                                  onClose={closeModal}
                                  onSubmit={handleAssignAttribute}
                                  onFetch={search}
                                  open={
                                    params.action === "assign-attribute" &&
                                    params.type === AttributeTypeEnum[key]
                                  }
                                  selected={maybe(() => params.ids, [])}
                                  onToggle={attributeId => {
                                    const ids = maybe(() => params.ids, []);
                                    navigate(
                                      productTypeUrl(id, {
                                        ...params,
                                        ids: ids.includes(id)
                                          ? params.ids.filter(
                                              selectedId =>
                                                selectedId !== attributeId
                                            )
                                          : [...ids, attributeId]
                                      })
                                    );
                                  }}
                                  key={key}
                                />
                              ))}
                            </>
                          )}
                        </SearchAttributes>
                      )}
                      <ProductTypeDeleteDialog
                        confirmButtonState={deleteTransactionState}
                        name={maybe(() => data.productType.name, "...")}
                        open={params.action === "remove"}
                        onClose={() => navigate(productTypeUrl(id))}
                        onConfirm={handleProductTypeDelete}
                      />
                      <ProductTypeBulkAttributeUnassignDialog
                        attributeQuantity={maybe(
                          () => params.ids.length.toString(),
                          "..."
                        )}
                        confirmButtonState={unassignTransactionState}
                        onClose={closeModal}
                        onConfirm={handleAttributeUnassign}
                        open={params.action === "unassign-attributes"}
                        productTypeName={maybe(
                          () => data.productType.name,
                          "..."
                        )}
                      />
                      <ProductTypeAttributeUnassignDialog
                        attributeName={maybe(
                          () =>
                            [
                              ...data.productType.productAttributes,
                              ...data.productType.variantAttributes
                            ].find(attribute => attribute.id === params.id)
                              .name,
                          "..."
                        )}
                        confirmButtonState={unassignTransactionState}
                        onClose={closeModal}
                        onConfirm={handleBulkAttributeUnassign}
                        open={params.action === "unassign-attribute"}
                        productTypeName={maybe(
                          () => data.productType.name,
                          "..."
                        )}
                      />
                    </>
                  );
                }}
              </ProductTypeOperations>
            );
          }}
        </TypedProductTypeDetailsQuery>
      )}
    </ProductTypeUpdateErrors>
  );
};
export default ProductTypeUpdate;
