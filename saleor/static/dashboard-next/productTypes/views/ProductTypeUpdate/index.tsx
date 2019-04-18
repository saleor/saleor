import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { WindowTitle } from "../../../components/WindowTitle";
import useNavigator from "../../../hooks/useNavigator";
import useNotifier from "../../../hooks/useNotifier";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import { AttributeTypeEnum } from "../../../types/globalTypes";
import ProductTypeAttributeEditDialog, {
  FormData as AttributeForm
} from "../../components/ProductTypeAttributeEditDialog";
import ProductTypeDetailsPage, {
  ProductTypeForm
} from "../../components/ProductTypeDetailsPage";
import ProductTypeOperations from "../../containers/ProductTypeOperations";
import { TypedProductTypeDetailsQuery } from "../../queries";
import { AttributeCreate } from "../../types/AttributeCreate";
import { AttributeDelete } from "../../types/AttributeDelete";
import { AttributeUpdate } from "../../types/AttributeUpdate";
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

export const ProductTypeUpdate: React.StatelessComponent<
  ProductTypeUpdateProps
> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  return (
    <ProductTypeUpdateErrors>
      {({ errors, set: setErrors }) => (
        <TypedProductTypeDetailsQuery
          displayLoader
          variables={{ id }}
          require={["productType"]}
        >
          {({ data, loading: dataLoading }) => {
            const closeModal = () => {
              navigate(productTypeUrl(id), true);
              setErrors.addAttributeErrors([]);
              setErrors.editAttributeErrors([]);
            };
            const handleAttributeCreateSuccess = (data: AttributeCreate) => {
              if (data.attributeCreate.errors.length === 0) {
                notify({
                  text: i18n.t("Attribute created", {
                    context: "notification"
                  })
                });
                closeModal();
              } else if (
                data.attributeCreate.errors !== null &&
                data.attributeCreate.errors.length > 0
              ) {
                setErrors.addAttributeErrors(data.attributeCreate.errors);
              }
            };
            const handleAttributeDeleteSuccess = (data: AttributeDelete) => {
              if (!data.attributeDelete.errors) {
                notify({
                  text: i18n.t("Attribute deleted", {
                    context: "notification"
                  })
                });
              }
            };
            const handleAttributeUpdateSuccess = (data: AttributeUpdate) => {
              if (data.attributeUpdate.errors.length === 0) {
                notify({
                  text: i18n.t("Attribute updated", {
                    context: "notification"
                  })
                });
                closeModal();
              } else if (
                data.attributeUpdate.errors !== null &&
                data.attributeUpdate.errors.length > 0
              ) {
                setErrors.editAttributeErrors(data.attributeUpdate.errors);
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
                onAttributeCreate={handleAttributeCreateSuccess}
                onAttributeDelete={handleAttributeDeleteSuccess}
                onAttributeUpdate={handleAttributeUpdateSuccess}
                onProductTypeDelete={handleProductTypeDeleteSuccess}
                onProductTypeUpdate={handleProductTypeUpdateSuccess}
              >
                {({
                  attributeCreate,
                  deleteAttribute,
                  deleteProductType,
                  updateAttribute,
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
                        taxRate: formData.taxRate,
                        variantAttributes: formData.variantAttributes.map(
                          choice => choice.value
                        ),
                        weight: formData.weight
                      }
                    });
                  };
                  const handleAttributeCreate = (
                    data: AttributeForm,
                    type: AttributeTypeEnum
                  ) =>
                    attributeCreate.mutate({
                      id,
                      input: {
                        name: data.name,
                        values: data.values.map(value => ({
                          name: value.label
                        }))
                      },
                      type
                    });
                  const handleAttributeDelete = (
                    id: string,
                    event: React.MouseEvent<any>
                  ) => {
                    event.stopPropagation();
                    deleteAttribute.mutate({ id });
                  };
                  const handleAttributeUpdate = (
                    id: string,
                    formData: AttributeForm
                  ) => {
                    const attribute = data.productType.variantAttributes
                      .concat(data.productType.productAttributes)
                      .filter(attribute => attribute.id === id)[0];
                    updateAttribute.mutate({
                      id,
                      input: {
                        addValues: formData.values
                          .filter(
                            value =>
                              !attribute.values
                                .map(value => value.id)
                                .includes(value.value)
                          )
                          .map(value => ({
                            name: value.label
                          })),
                        name: formData.name,
                        removeValues: attribute.values
                          .filter(
                            value =>
                              !formData.values
                                .map(value => value.value)
                                .includes(value.id)
                          )
                          .map(value => value.id)
                      }
                    });
                  };
                  const loading = updateProductType.opts.loading || dataLoading;
                  const deleteTransactionState = getMutationState(
                    deleteProductType.opts.called,
                    deleteProductType.opts.loading,
                    maybe(
                      () => deleteProductType.opts.data.productTypeDelete.errors
                    )
                  );

                  const attribute = maybe(() =>
                    data.productType.productAttributes
                      .concat(data.productType.variantAttributes)
                      .find(attribute => attribute.id === params.id)
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
                        saveButtonBarState={loading ? "loading" : "default"}
                        onAttributeAdd={type =>
                          navigate(
                            productTypeUrl(id, {
                              action: "add-attribute",
                              type
                            })
                          )
                        }
                        onAttributeDelete={handleAttributeDelete}
                        onAttributeUpdate={attributeId =>
                          navigate(
                            productTypeUrl(id, {
                              action: "edit-attribute",
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
                      />
                      {!dataLoading && (
                        <>
                          {Object.keys(AttributeTypeEnum).map(key => (
                            <ProductTypeAttributeEditDialog
                              disabled={attributeCreate.opts.loading}
                              errors={errors.addAttributeErrors}
                              name=""
                              values={[]}
                              onClose={closeModal}
                              onConfirm={data =>
                                handleAttributeCreate(
                                  data,
                                  AttributeTypeEnum[key]
                                )
                              }
                              opened={
                                params.action === "add-attribute" &&
                                params.type === AttributeTypeEnum[key]
                              }
                              title={i18n.t("Add Attribute", {
                                context: "modal title"
                              })}
                              key={key}
                            />
                          ))}
                          <ProductTypeAttributeEditDialog
                            disabled={updateAttribute.opts.loading}
                            errors={errors.editAttributeErrors}
                            name={maybe(() => attribute.name)}
                            values={maybe(() =>
                              attribute.values.map(value => ({
                                label: value.name,
                                value: value.id
                              }))
                            )}
                            onClose={closeModal}
                            onConfirm={data =>
                              handleAttributeUpdate(params.id, data)
                            }
                            opened={params.action === "edit-attribute"}
                            title={i18n.t("Edit Attribute", {
                              context: "modal title"
                            })}
                          />
                          <ActionDialog
                            confirmButtonState={deleteTransactionState}
                            open={params.action === "remove"}
                            onClose={() => navigate(productTypeUrl(id))}
                            onConfirm={handleProductTypeDelete}
                            title={i18n.t("Remove product type")}
                            variant="delete"
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ name }}</strong>?",
                                  {
                                    name: maybe(
                                      () => data.productType.name,
                                      "..."
                                    )
                                  }
                                )
                              }}
                            />
                          </ActionDialog>
                        </>
                      )}
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
