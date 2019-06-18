import * as React from "react";

import useNavigator from "@saleor/hooks/useNavigator";
import useNotifier from "@saleor/hooks/useNotifier";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import AttributeDeleteDialog from "../../components/AttributeDeleteDialog";
import AttributePage from "../../components/AttributePage";
import { AttributeDetailsQuery } from "../../queries";
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
        action: undefined
      }),
      true
    );

  const openModal = (action: AttributeUrlDialog) =>
    navigate(
      attributeUrl(id, {
        ...params,
        action
      })
    );

  const handleDelete = () => {
    notify({ text: i18n.t("Product removed") });
    navigate(attributeListUrl());
  };
  const handleUpdate = () => notify({ text: i18n.t("Saved changes") });

  return (
    <AttributeDetailsQuery variables={{ id }}>
      {({ data, loading }) => (
        <>
          <AttributePage
            attribute={maybe(() => data.attribute)}
            disabled={loading}
            onBack={() => navigate(attributeListUrl())}
            onDelete={() => openModal("remove")}
            onSubmit={() => undefined}
            onValueAdd={() => openModal("add-value")}
            onValueDelete={() => openModal("remove-value")}
            onValueUpdate={() => openModal("edit-value")}
            saveButtonBarState={"default"}
            values={maybe(() => data.attribute.values)}
          />
          <AttributeDeleteDialog
            open={params.action === "remove"}
            name={maybe(() => data.attribute.name, "...")}
            confirmButtonState="default"
            onClose={closeModal}
            onConfirm={() => undefined}
          />
        </>
      )}
    </AttributeDetailsQuery>
  );
};
AttributeDetails.displayName = "AttributeDetails";

export default AttributeDetails;
