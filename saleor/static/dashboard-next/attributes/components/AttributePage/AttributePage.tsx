import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { UserError } from "@saleor/types";
import {
  AttributeDetailsFragment,
  AttributeDetailsFragment_values
} from "../../types/AttributeDetailsFragment";
import AttributeDetails from "../AttributeDetails";
import AttributeValues from "../AttributeValues";

export interface AttributePageProps {
  attribute: AttributeDetailsFragment | null;
  disabled: boolean;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  values: AttributeDetailsFragment_values[];
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: AttributePageFormData) => void;
  onValueAdd: () => void;
  onValueDelete: (id: string) => void;
  onValueUpdate: (id: string) => void;
}

export interface AttributePageFormData {
  name: string;
  slug: string;
}

const AttributePage: React.FC<AttributePageProps> = ({
  attribute,
  disabled,
  errors,
  saveButtonBarState,
  values,
  onBack,
  onDelete,
  onSubmit,
  onValueAdd,
  onValueDelete,
  onValueUpdate
}) => {
  const initialForm: AttributePageFormData =
    attribute === null
      ? {
          name: "",
          slug: ""
        }
      : {
          name: maybe(() => attribute.name, ""),
          slug: maybe(() => attribute.slug, "")
        };

  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, errors: formErrors, data, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Attributes")}</AppHeader>
          <PageHeader
            title={
              attribute === null
                ? i18n.t("Create New Attribute", {
                    context: "page title"
                  })
                : maybe(() => attribute.name)
            }
          />
          <Grid>
            <div>
              <AttributeDetails
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <AttributeValues
                disabled={disabled}
                values={values}
                onValueAdd={onValueAdd}
                onValueDelete={onValueDelete}
                onValueUpdate={onValueUpdate}
              />
            </div>
            {/* TODO: Uncomment after restricting some attributes to be only product attributes */}
            {/* <div>
              <AttributeProperties
                data={data}
                disabled={disabled}
                onChange={change}
              />
            </div> */}
          </Grid>
          <SaveButtonBar
            disabled={disabled}
            state={saveButtonBarState}
            onCancel={onBack}
            onSave={submit}
            onDelete={attribute === null ? undefined : onDelete}
          />
        </Container>
      )}
    </Form>
  );
};
AttributePage.displayName = "AttributePage";
export default AttributePage;
