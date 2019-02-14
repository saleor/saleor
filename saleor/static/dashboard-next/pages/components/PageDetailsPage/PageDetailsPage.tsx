import { RawDraftContentState } from "draft-js";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import { maybe } from "../../../misc";
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
  page: PageDetails_page;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
}

const PageDetailsPage: React.StatelessComponent<PageDetailsPageProps> = ({
  disabled,
  page,
  saveButtonBarState,
  onBack,
  onRemove,
  onSubmit
}) => {
  const initialForm: FormData = {
    availableOn: maybe(() => page.availableOn, ""),
    content: maybe(() => JSON.parse(page.content)),
    isVisible: maybe(() => page.isVisible, false),
    seoDescription: maybe(() => page.seoDescription, ""),
    seoTitle: maybe(() => page.seoTitle, ""),
    slug: maybe(() => page.slug, ""),
    title: maybe(() => page.title, "")
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => page.title)} onBack={onBack} />
          <Grid>
            <div>
              <PageInfo
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <SeoForm
                description={data.seoDescription}
                disabled={disabled}
                descriptionPlaceholder={data.title}
                onChange={change}
                title={data.seoTitle}
                titlePlaceholder={data.title}
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
            onDelete={onRemove}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
PageDetailsPage.displayName = "PageDetailsPage";
export default PageDetailsPage;
