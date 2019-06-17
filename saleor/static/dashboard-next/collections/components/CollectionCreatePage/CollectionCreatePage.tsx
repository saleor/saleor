import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { ContentState, convertToRaw, RawDraftContentState } from "draft-js";
import * as React from "react";

import AppHeader from "@saleor/components/AppHeader";
import { CardSpacer } from "@saleor/components/CardSpacer";
import CardTitle from "@saleor/components/CardTitle";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import { Container } from "@saleor/components/Container";
import Form from "@saleor/components/Form";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import SeoForm from "@saleor/components/SeoForm";
import VisibilityCard from "@saleor/components/VisibilityCard";
import i18n from "../../../i18n";
import { UserError } from "../../../types";
import CollectionDetails from "../CollectionDetails/CollectionDetails";
import { CollectionImage } from "../CollectionImage/CollectionImage";

export interface CollectionCreatePageFormData {
  backgroundImage: {
    url: string;
    value: string;
  };
  backgroundImageAlt: string;
  description: RawDraftContentState;
  name: string;
  publicationDate: string;
  isPublished: boolean;
  seoDescription: string;
  seoTitle: string;
}

export interface CollectionCreatePageProps {
  disabled: boolean;
  errors: UserError[];
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onSubmit: (data: CollectionCreatePageFormData) => void;
}

const initialForm: CollectionCreatePageFormData = {
  backgroundImage: {
    url: null,
    value: null
  },
  backgroundImageAlt: "",
  description: convertToRaw(ContentState.createFromText("")),
  isPublished: false,
  name: "",
  publicationDate: "",
  seoDescription: "",
  seoTitle: ""
};

const CollectionCreatePage: React.StatelessComponent<
  CollectionCreatePageProps
> = ({
  disabled,
  errors,
  saveButtonBarState,
  onBack,
  onSubmit
}: CollectionCreatePageProps) => (
  <Form errors={errors} initial={initialForm} onSubmit={onSubmit}>
    {({ change, data, errors: formErrors, hasChanged, submit }) => (
      <Container>
        <AppHeader onBack={onBack}>{i18n.t("Collections")}</AppHeader>
        <PageHeader
          title={i18n.t("Add collection", {
            context: "page title"
          })}
        />
        <Grid>
          <div>
            <CollectionDetails
              data={data}
              disabled={disabled}
              errors={formErrors}
              onChange={change}
            />
            <CardSpacer />
            <CollectionImage
              image={
                data.backgroundImage.url
                  ? {
                      __typename: "Image",
                      alt: data.backgroundImageAlt,
                      url: data.backgroundImage.url
                    }
                  : null
              }
              onImageDelete={() =>
                change({
                  target: {
                    name: "backgroundImage",
                    value: {
                      url: null,
                      value: null
                    }
                  }
                } as any)
              }
              onImageUpload={file =>
                change({
                  target: {
                    name: "backgroundImage",
                    value: {
                      url: URL.createObjectURL(file),
                      value: file
                    }
                  }
                } as any)
              }
              onChange={change}
              data={data}
            />
            <CardSpacer />
            <SeoForm
              description={data.seoDescription}
              disabled={disabled}
              descriptionPlaceholder=""
              helperText={i18n.t(
                "Add search engine title and description to make this collection easier to find",
                {
                  context: "help text"
                }
              )}
              title={data.seoTitle}
              titlePlaceholder={data.name}
              onChange={change}
            />
          </div>
          <div>
            <div>
              <Card>
                <CardTitle
                  title={i18n.t("Availability", {
                    context: "collection status"
                  })}
                />
                <CardContent>
                  <VisibilityCard
                    data={data}
                    errors={formErrors}
                    disabled={disabled}
                    onChange={change}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </Grid>
        <SaveButtonBar
          state={saveButtonBarState}
          disabled={disabled || !hasChanged}
          onCancel={onBack}
          onSave={submit}
        />
      </Container>
    )}
  </Form>
);
CollectionCreatePage.displayName = "CollectionCreatePage";
export default CollectionCreatePage;
