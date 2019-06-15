import {
  ContentState,
  convertFromRaw,
  convertToRaw,
  RawDraftContentState
} from "draft-js";
import * as React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardSpacer from "@saleor/components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import Container from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import SeoForm from "@saleor/components/SeoForm";
import VisibilityCard from "@saleor/components/VisibilityCard";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { UserError } from "../../../types";
import { PageDetails_page } from "../../types/PageDetails";
import PageInfo from "../PageInfo";
import PageSlug from "../PageSlug";

export interface FormData {
  content: RawDraftContentState;
  isPublished: boolean;
  publicationDate: string;
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
    content: maybe(
      () => JSON.parse(page.contentJson),
      convertToRaw(ContentState.createFromText(""))
    ),
    isPublished: maybe(() => page.isPublished, false),
    publicationDate: maybe(() => page.publicationDate, ""),
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
              <VisibilityCard
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
