import React from "react";
import slugify from "slugify";

import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "@saleor/i18n";
import { getMutationState, maybe } from "@saleor/misc";
import { ReorderEvent, UserError } from "@saleor/types";
import {
  add,
  isSelected,
  move,
  remove,
  updateAtIndex
} from "@saleor/utils/lists";
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

function areValuesEqual(
  a: AttributeValueEditDialogFormData,
  b: AttributeValueEditDialogFormData
) {
  return a.name === b.name;
}

const AttributeDetails: React.FC<AttributeDetailsProps> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const [values, setValues] = React.useState<
    AttributeValueEditDialogFormData[]
  >([]);
  const [valueErrors, setValueErrors] = React.useState<UserError[]>([]);

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
    setValues(remove(values[params.id], values, areValuesEqual));
    closeModal();
  };
  const handleCreate = (data: AttributeCreate) => {
    if (data.attributeCreate.errors.length === 0) {
      notify({ text: i18n.t("Successfully created attribute") });
      navigate(attributeUrl(data.attributeCreate.attribute.id));
    }
  };
  const handleValueUpdate = (input: AttributeValueEditDialogFormData) => {
    if (isSelected(input, values, areValuesEqual)) {
      setValueErrors([
        {
          field: "name",
          message: i18n.t("A value named {{ name }} already exists", {
            context: "value edit error",
            name: input.name
          })
        }
      ]);
    } else {
      setValues(updateAtIndex(input, values, id));
      closeModal();
    }
  };
  const handleValueCreate = (input: AttributeValueEditDialogFormData) => {
    if (isSelected(input, values, areValuesEqual)) {
      setValueErrors([
        {
          field: "name",
          message: i18n.t("A value named {{ name }} already exists", {
            context: "value edit error",
            name: input.name
          })
        }
      ]);
    } else {
      setValues(add(input, values));
      closeModal();
    }
  };
  const handleValueReorder = ({ newIndex, oldIndex }: ReorderEvent) =>
    setValues(move(values[oldIndex], values, areValuesEqual, newIndex));

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
              errors={maybe(
                () => attributeCreateOpts.data.attributeCreate.errors,
                []
              )}
              onBack={() => navigate(attributeListUrl())}
              onDelete={undefined}
              onSubmit={input =>
                attributeCreate({
                  variables: {
                    input: {
                      ...input,
                      storefrontSearchPosition: parseInt(
                        input.storefrontSearchPosition,
                        0
                      ),
                      values: values.map(value => ({
                        name: value.name
                      }))
                    }
                  }
                })
              }
              onValueAdd={() => openModal("add-value")}
              onValueDelete={id => openModal("remove-value", id)}
              onValueReorder={handleValueReorder}
              onValueUpdate={id => openModal("edit-value", id)}
              saveButtonBarState={createTransitionState}
              values={values.map((value, valueIndex) => ({
                __typename: "AttributeValue" as "AttributeValue",
                id: valueIndex.toString(),
                slug: slugify(value.name).toLowerCase(),
                sortOrder: valueIndex,
                type: null,
                value: null,
                ...value
              }))}
            />
            <AttributeValueEditDialog
              attributeValue={null}
              confirmButtonState="default"
              disabled={false}
              errors={valueErrors}
              open={params.action === "add-value"}
              onClose={closeModal}
              onSubmit={handleValueCreate}
            />
            {values.length > 0 && (
              <>
                <AttributeValueDeleteDialog
                  attributeName={undefined}
                  open={params.action === "remove-value"}
                  name={maybe(() => values[id].name, "...")}
                  confirmButtonState="default"
                  onClose={closeModal}
                  onConfirm={handleValueDelete}
                />
                <AttributeValueEditDialog
                  attributeValue={maybe(() => values[params.id])}
                  confirmButtonState="default"
                  disabled={false}
                  errors={valueErrors}
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
