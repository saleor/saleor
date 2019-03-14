import {
  ContentState,
  convertFromRaw,
  convertToRaw,
  RawDraftContentState
} from "draft-js";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { PageDetails_page } from "../../types/PageDetails";
import PageAvailability from "../PageAvailability";
import PageInfo from "../PageInfo";
import PageSlug from "../PageSlug";

export interface FormData {
  availableOn: string;
  content: RawDraftContentState;
  isVisible: boolean;
  seoDescription: string;
  seoTitle: string;
  slug: string;
  title: string;
}

export interface PageDetailsPageProps {
  disabled: boolean;
  errors: UserError[];
  page: PageDetails_page;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
}

const PageDetailsPage: React.StatelessComponent<PageDetailsPageProps> = ({
  disabled,
  errors,
  page,
  saveButtonBarState,
  onBack,
  onRemove,
  onSubmit
}) => {
  const initialForm: FormData = {
    availableOn: maybe(() => page.availableOn, ""),
    content: maybe(
      () => JSON.parse(page.contentJson),
      convertToRaw(ContentState.createFromText(""))
    ),
    isVisible: maybe(() => page.isVisible, false),
    seoDescription: maybe(() => page.seoDescription || "", ""),
    seoTitle: maybe(() => page.seoTitle || "", ""),
    slug: maybe(() => page.slug, ""),
    title: maybe(() => page.title, "")
  };
  return (
    <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Pages")}</AppHeader>
          <PageHeader
            title={
              page === null
                ? i18n.t("Add Page", {
                    context: "header"
                  })
                : maybe(() => page.title)
            }
          />
          <Grid>
            <div>
              <PageInfo
                data={data}
                disabled={disabled}
                errors={formErrors}
                page={page}
                onChange={change}
              />
              <CardSpacer />
              <SeoForm
                description={data.seoDescription}
                disabled={disabled}
                descriptionPlaceholder={maybe(() => {
                  return convertFromRaw(data.content)
                    .getPlainText()
                    .slice(0, 300);
                }, "")}
                onChange={change}
                title={data.seoTitle}
                titlePlaceholder={data.title}
                helperText={i18n.t(
                  "Add search engine title and description to make this page easier to find"
                )}
              />
            </div>
            <div>
              <PageSlug
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <PageAvailability
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
            </div>
          </Grid>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            state={saveButtonBarState}
            onCancel={onBack}
            onDelete={page === null ? undefined : onRemove}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
PageDetailsPage.displayName = "PageDetailsPage";
export default PageDetailsPage;
