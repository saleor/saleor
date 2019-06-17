import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import {
  AttributeDetailsFragment,
  AttributeDetailsFragment_values
} from "../../types/AttributeDetailsFragment";
import AttributeDetails from "../AttributeDetails";
import AttributeValues from "../AttributeValues";

export interface AttributePageProps {
  attribute: AttributeDetailsFragment | null;
  disabled: boolean;
  saveButtonBarState: ConfirmButtonTransitionState;
  values: AttributeDetailsFragment_values[];
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: AttributePageFormData) => void;
  onValueAdd: () => void;
  onValueDelete: (id: string, event: React.MouseEvent<any>) => void;
  onValueUpdate: (id: string) => void;
}

export interface AttributePageFormData {
  name: string;
  slug: string;
}

const AttributePage: React.FC<AttributePageProps> = ({
  attribute,
  disabled,
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
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, submit }) => (
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
