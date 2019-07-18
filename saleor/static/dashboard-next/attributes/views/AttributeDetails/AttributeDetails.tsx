import React from "react";

import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import AttributeDeleteDialog from "../../components/AttributeDeleteDialog";
import AttributePage from "../../components/AttributePage";
import AttributeValueDeleteDialog from "../../components/AttributeValueDeleteDialog";
import AttributeValueEditDialog from "../../components/AttributeValueEditDialog";
import {
  AttributeDeleteMutation,
  AttributeUpdateMutation,
  AttributeValueCreateMutation,
  AttributeValueDeleteMutation,
  AttributeValueUpdateMutation
} from "../../mutations";
import { AttributeDetailsQuery } from "../../queries";
import { AttributeDelete } from "../../types/AttributeDelete";
import { AttributeUpdate } from "../../types/AttributeUpdate";
import { AttributeValueCreate } from "../../types/AttributeValueCreate";
import { AttributeValueDelete } from "../../types/AttributeValueDelete";
import { AttributeValueUpdate } from "../../types/AttributeValueUpdate";
import {
  attributeListUrl,
  attributeUrl,
  AttributeUrlDialog,
  AttributeUrlQueryParams
} from "../../urls";

interface AttributeDetailsProps {
  id: string;
  params: AttributeUrlQueryParams;
}

const AttributeDetails: React.FC<AttributeDetailsProps> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const closeModal = () =>
    navigate(
      attributeUrl(id, {
        ...params,
        action: undefined,
        id: undefined,
        ids: undefined
      }),
      true
    );

  const openModal = (action: AttributeUrlDialog, valueId?: string) =>
    navigate(
      attributeUrl(id, {
        ...params,
        action,
        id: valueId
      })
    );

  const handleDelete = (data: AttributeDelete) => {
    if (data.attributeDelete.errors.length === 0) {
      notify({ text: i18n.t("Attribute removed") });
      navigate(attributeListUrl());
    }
  };
  const handleValueDelete = (data: AttributeValueDelete) => {
    if (data.attributeValueDelete.errors.length === 0) {
      notify({ text: i18n.t("Value removed") });
      closeModal();
    }
  };
  const handleUpdate = (data: AttributeUpdate) => {
    if (data.attributeUpdate.errors.length === 0) {
      notify({ text: i18n.t("Saved changes") });
    }
  };
  const handleValueUpdate = (data: AttributeValueUpdate) => {
    if (data.attributeValueUpdate.errors.length === 0) {
      notify({ text: i18n.t("Saved changes") });
      closeModal();
    }
  };
  const handleValueCreate = (data: AttributeValueCreate) => {
    if (data.attributeValueCreate.errors.length === 0) {
      notify({ text: i18n.t("Added new value") });
      closeModal();
    }
  };

  return (
    <AttributeDetailsQuery variables={{ id }}>
      {({ data, loading }) => (
        <AttributeDeleteMutation onCompleted={handleDelete}>
          {(attributeDelete, attributeDeleteOpts) => (
            <AttributeValueDeleteMutation onCompleted={handleValueDelete}>
              {(attributeValueDelete, attributeValueDeleteOpts) => (
                <AttributeUpdateMutation onCompleted={handleUpdate}>
                  {(attributeUpdate, attributeUpdateOpts) => (
                    <AttributeValueUpdateMutation
                      onCompleted={handleValueUpdate}
                    >
                      {(attributeValueUpdate, attributeValueUpdateOpts) => (
                        <AttributeValueCreateMutation
                          onCompleted={handleValueCreate}
                        >
                          {(attributeValueCreate, attributeValueCreateOpts) => {
                            const deleteTransitionState = getMutationState(
                              attributeDeleteOpts.called,
                              attributeDeleteOpts.loading,
                              maybe(
                                () =>
                                  attributeDeleteOpts.data.attributeDelete
                                    .errors
                              )
                            );
                            const deleteValueTransitionState = getMutationState(
                              attributeValueDeleteOpts.called,
                              attributeValueDeleteOpts.loading,
                              maybe(
                                () =>
                                  attributeValueDeleteOpts.data
                                    .attributeValueDelete.errors
                              )
                            );
                            const updateTransitionState = getMutationState(
                              attributeUpdateOpts.called,
                              attributeUpdateOpts.loading,
                              maybe(
                                () =>
                                  attributeUpdateOpts.data.attributeUpdate
                                    .errors
                              )
                            );
                            const updateValueTransitionState = getMutationState(
                              attributeValueUpdateOpts.called,
                              attributeValueUpdateOpts.loading,
                              maybe(
                                () =>
                                  attributeValueUpdateOpts.data
                                    .attributeValueUpdate.errors
                              )
                            );
                            const createValueTransitionState = getMutationState(
                              attributeValueCreateOpts.called,
                              attributeValueCreateOpts.loading,
                              maybe(
                                () =>
                                  attributeValueCreateOpts.data
                                    .attributeValueCreate.errors
                              )
                            );

                            return (
                              <>
                                <AttributePage
                                  attribute={maybe(() => data.attribute)}
                                  disabled={loading}
                                  errors={maybe(
                                    () =>
                                      attributeUpdateOpts.data.attributeUpdate
                                        .errors,
                                    []
                                  )}
                                  onBack={() => navigate(attributeListUrl())}
                                  onDelete={() => openModal("remove")}
                                  onSubmit={data => {
                                    const input = {
                                      ...data,
                                      inputType: undefined
                                    };

                                    attributeUpdate({
                                      variables: {
                                        id,
                                        input: {
                                          ...input,
                                          storefrontSearchPosition: parseInt(
                                            input.storefrontSearchPosition,
                                            0
                                          )
                                        }
                                      }
                                    });
                                  }}
                                  onValueAdd={() => openModal("add-value")}
                                  onValueDelete={id =>
                                    openModal("remove-value", id)
                                  }
                                  onValueReorder={() => undefined}
                                  onValueUpdate={id =>
                                    openModal("edit-value", id)
                                  }
                                  saveButtonBarState={updateTransitionState}
                                  values={maybe(() => data.attribute.values)}
                                />
                                <AttributeDeleteDialog
                                  open={params.action === "remove"}
                                  name={maybe(() => data.attribute.name, "...")}
                                  confirmButtonState={deleteTransitionState}
                                  onClose={closeModal}
                                  onConfirm={() =>
                                    attributeDelete({
                                      variables: {
                                        id
                                      }
                                    })
                                  }
                                />
                                <AttributeValueDeleteDialog
                                  attributeName={maybe(
                                    () => data.attribute.name,
                                    "..."
                                  )}
                                  open={params.action === "remove-value"}
                                  name={maybe(
                                    () =>
                                      data.attribute.values.find(
                                        value => params.id === value.id
                                      ).name,
                                    "..."
                                  )}
                                  useName={true}
                                  confirmButtonState={
                                    deleteValueTransitionState
                                  }
                                  onClose={closeModal}
                                  onConfirm={() =>
                                    attributeValueDelete({
                                      variables: {
                                        id: params.id
                                      }
                                    })
                                  }
                                />
                                <AttributeValueEditDialog
                                  attributeValue={null}
                                  confirmButtonState={
                                    createValueTransitionState
                                  }
                                  disabled={loading}
                                  errors={maybe(
                                    () =>
                                      attributeValueCreateOpts.data
                                        .attributeValueCreate.errors,
                                    []
                                  )}
                                  open={params.action === "add-value"}
                                  onClose={closeModal}
                                  onSubmit={input =>
                                    attributeValueCreate({
                                      variables: {
                                        id,
                                        input: {
                                          name: input.name,
                                          value: input.slug
                                        }
                                      }
                                    })
                                  }
                                />
                                <AttributeValueEditDialog
                                  attributeValue={maybe(() =>
                                    data.attribute.values.find(
                                      value => params.id === value.id
                                    )
                                  )}
                                  confirmButtonState={
                                    updateValueTransitionState
                                  }
                                  disabled={loading}
                                  errors={maybe(
                                    () =>
                                      attributeValueUpdateOpts.data
                                        .attributeValueUpdate.errors,
                                    []
                                  )}
                                  open={params.action === "edit-value"}
                                  onClose={closeModal}
                                  onSubmit={input =>
                                    attributeValueUpdate({
                                      variables: {
                                        id: data.attribute.values.find(
                                          value => params.id === value.id
                                        ).id,
                                        input: {
                                          name: input.name,
                                          value: input.slug
                                        }
                                      }
                                    })
                                  }
                                />
                              </>
                            );
                          }}
                        </AttributeValueCreateMutation>
                      )}
                    </AttributeValueUpdateMutation>
                  )}
                </AttributeUpdateMutation>
              )}
            </AttributeValueDeleteMutation>
          )}
        </AttributeDeleteMutation>
      )}
    </AttributeDetailsQuery>
  );
};
AttributeDetails.displayName = "AttributeDetails";

export default AttributeDetails;
