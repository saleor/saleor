import * as React from "react";

import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import AttributePage from "../../components/AttributePage";
import AttributeValueDeleteDialog from "../../components/AttributeValueDeleteDialog";
import AttributeValueEditDialog, {
  AttributeValueEditDialogFormData
} from "../../components/AttributeValueEditDialog";
import { AttributeCreateMutation } from "../../mutations";
import { AttributeCreate } from "../../types/AttributeCreate";
import {
  attributeAddUrl,
  AttributeAddUrlDialog,
  AttributeAddUrlQueryParams,
  attributeListUrl,
  attributeUrl
} from "../../urls";

interface AttributeDetailsProps {
  params: AttributeAddUrlQueryParams;
}

const AttributeDetails: React.FC<AttributeDetailsProps> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const [values, setValues] = React.useState<
    AttributeValueEditDialogFormData[]
  >([]);

  const id = params.id ? parseInt(params.id, 0) : undefined;

  const closeModal = () =>
    navigate(
      attributeAddUrl({
        ...params,
        action: undefined,
        id: undefined
      }),
      true
    );

  const openModal = (action: AttributeAddUrlDialog, valueId?: string) =>
    navigate(
      attributeAddUrl({
        ...params,
        action,
        id: valueId
      })
    );

  const handleValueDelete = () => {
    setValues([...values.slice(0, id), ...values.slice(id + 1)]);
    notify({ text: i18n.t("Value removed") });
    closeModal();
  };
  const handleCreate = (data: AttributeCreate) => {
    if (data.attributeCreate.errors.length === 0) {
      notify({ text: i18n.t("Successfully created attribute") });
      navigate(attributeUrl(data.attributeCreate.attribute.id));
    }
  };
  const handleValueUpdate = (input: AttributeValueEditDialogFormData) => {
    setValues([...values.slice(0, id), input, ...values.slice(id + 1)]);
    notify({ text: i18n.t("Saved changes") });
    closeModal();
  };
  const handleValueCreate = (input: AttributeValueEditDialogFormData) => {
    setValues([...values, input]);
    notify({ text: i18n.t("Added new value") });
    closeModal();
  };

  return (
    <AttributeCreateMutation onCompleted={handleCreate}>
      {(attributeCreate, attributeCreateOpts) => {
        const createTransitionState = getMutationState(
          attributeCreateOpts.called,
          attributeCreateOpts.loading,
          maybe(() => attributeCreateOpts.data.attributeCreate.errors)
        );

        return (
          <>
            <AttributePage
              attribute={null}
              disabled={false}
              onBack={() => navigate(attributeListUrl())}
              onDelete={undefined}
              onSubmit={input =>
                attributeCreate({
                  variables: {
                    input: {
                      ...input,
                      values: values.map(value => ({
                        name: value.name,
                        value: value.slug
                      }))
                    }
                  }
                })
              }
              onValueAdd={() => openModal("add-value")}
              onValueDelete={id => openModal("remove-value", id)}
              onValueUpdate={id => openModal("edit-value", id)}
              saveButtonBarState={createTransitionState}
              values={values.map((value, valueIndex) => ({
                __typename: "AttributeValue",
                id: valueIndex.toString(),
                sortOrder: null,
                type: null,
                value: null,
                ...value
              }))}
            />
            <AttributeValueEditDialog
              attributeValue={null}
              confirmButtonState="default"
              disabled={false}
              open={params.action === "add-value"}
              onClose={closeModal}
              onSubmit={handleValueCreate}
            />
            {values.length && (
              <>
                <AttributeValueDeleteDialog
                  open={params.action === "remove-value"}
                  name={maybe(() => values[id].name)}
                  confirmButtonState="default"
                  onClose={closeModal}
                  onConfirm={handleValueDelete}
                />
                <AttributeValueEditDialog
                  attributeValue={maybe(() => values[params.id])}
                  confirmButtonState="default"
                  disabled={false}
                  open={params.action === "edit-value"}
                  onClose={closeModal}
                  onSubmit={handleValueUpdate}
                />
              </>
            )}
          </>
        );
      }}
    </AttributeCreateMutation>
  );
};
AttributeDetails.displayName = "AttributeDetails";

export default AttributeDetails;
