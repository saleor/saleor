import { RawDraftContentState } from "draft-js";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import { CardSpacer } from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import CategoryDetailsForm from "../../components/CategoryDetailsForm";

interface FormData {
  description: RawDraftContentState;
  name: string;
  seoTitle: string;
  seoDescription: string;
}

const initialData: FormData = {
  description: null,
  name: "",
  seoDescription: "",
  seoTitle: ""
};

export interface CategoryCreatePageProps {
  errors: UserError[];
  disabled: boolean;
  saveButtonBarState: ConfirmButtonTransitionState;
  onSubmit(data: FormData);
  onBack();
}

export const CategoryCreatePage: React.StatelessComponent<
  CategoryCreatePageProps
> = ({
  disabled,
  onSubmit,
  onBack,
  errors: userErrors,
  saveButtonBarState
}) => (
  <Form
    onSubmit={onSubmit}
    initial={initialData}
    errors={userErrors}
    confirmLeave
  >
    {({ data, change, errors, submit, hasChanged }) => (
      <Container>
        <AppHeader onBack={onBack}>{i18n.t("Categories")}</AppHeader>
        <PageHeader title={i18n.t("Add Category")} />
        <div>
          <CategoryDetailsForm
            disabled={disabled}
            data={data}
            onChange={change}
            errors={errors}
          />
          <CardSpacer />
          <SeoForm
            helperText={i18n.t(
              "Add search engine title and description to make this product easier to find"
            )}
            title={data.seoTitle}
            titlePlaceholder={data.name}
            description={data.seoDescription}
            descriptionPlaceholder={data.name}
            loading={disabled}
            onChange={change}
            disabled={disabled}
          />
          <SaveButtonBar
            onCancel={onBack}
            onSave={submit}
            labels={{
              save: i18n.t("Save category")
            }}
            state={saveButtonBarState}
            disabled={disabled || !hasChanged}
          />
        </div>
      </Container>
    )}
  </Form>
);
CategoryCreatePage.displayName = "CategoryCreatePage";
export default CategoryCreatePage;
