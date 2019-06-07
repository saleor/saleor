import { RawDraftContentState } from "draft-js";
import * as React from "react";

import AppHeader from "@saleor-components/AppHeader";
import { CardSpacer } from "@saleor-components/CardSpacer";
import { ConfirmButtonTransitionState } from "@saleor-components/ConfirmButton";
import { Container } from "@saleor-components/Container";
import { ControlledSwitch } from "@saleor-components/ControlledSwitch";
import Form from "@saleor-components/Form";
import Grid from "@saleor-components/Grid";
import PageHeader from "@saleor-components/PageHeader";
import SaveButtonBar from "@saleor-components/SaveButtonBar";
import SeoForm from "@saleor-components/SeoForm";
import VisibilityCard from "@saleor-components/VisibilityCard";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListActions, PageListProps } from "../../../types";
import { CollectionDetails_collection } from "../../types/CollectionDetails";
import CollectionDetails from "../CollectionDetails/CollectionDetails";
import { CollectionImage } from "../CollectionImage/CollectionImage";
import CollectionProducts from "../CollectionProducts/CollectionProducts";

export interface CollectionDetailsPageFormData {
  backgroundImageAlt: string;
  description: RawDraftContentState;
  name: string;
  publicationDate: string;
  seoDescription: string;
  seoTitle: string;
  isFeatured: boolean;
  isPublished: boolean;
}

export interface CollectionDetailsPageProps extends PageListProps, ListActions {
  collection: CollectionDetails_collection;
  isFeatured: boolean;
  saveButtonBarState: ConfirmButtonTransitionState;
  onBack: () => void;
  onCollectionRemove: () => void;
  onImageDelete: () => void;
  onImageUpload: (file: File) => void;
  onProductUnassign: (id: string, event: React.MouseEvent<any>) => void;
  onSubmit: (data: CollectionDetailsPageFormData) => void;
}

const CollectionDetailsPage: React.StatelessComponent<
  CollectionDetailsPageProps
> = ({
  collection,
  disabled,
  isFeatured,
  saveButtonBarState,
  onBack,
  onCollectionRemove,
  onImageDelete,
  onImageUpload,
  onSubmit,
  ...collectionProductsProps
}: CollectionDetailsPageProps) => {
  return (
    <Form
      initial={{
        backgroundImageAlt: maybe(() => collection.backgroundImage.alt, ""),
        description: maybe(() => JSON.parse(collection.descriptionJson)),
        isFeatured,
        isPublished: maybe(() => collection.isPublished, false),
        name: maybe(() => collection.name, ""),
        publicationDate: maybe(() => collection.publicationDate, ""),
        seoDescription: maybe(() => collection.seoDescription, ""),
        seoTitle: maybe(() => collection.seoTitle, "")
      }}
      onSubmit={onSubmit}
      confirmLeave
    >
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container>
          <AppHeader onBack={onBack}>{i18n.t("Collections")}</AppHeader>
          <PageHeader title={maybe(() => collection.name)} />
          <Grid>
            <div>
              <CollectionDetails
                collection={collection}
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <CollectionImage
                data={data}
                image={maybe(() => collection.backgroundImage)}
                onImageDelete={onImageDelete}
                onImageUpload={onImageUpload}
                onChange={change}
              />
              <CardSpacer />
              <CollectionProducts
                disabled={disabled}
                collection={collection}
                {...collectionProductsProps}
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
                titlePlaceholder={maybe(() => collection.name)}
                onChange={change}
              />
            </div>
            <div>
              <div>
                <VisibilityCard
                  data={data}
                  errors={formErrors}
                  disabled={disabled}
                  onChange={change}
                >
                  <ControlledSwitch
                    checked={data.isFeatured}
                    disabled={disabled}
                    name="isFeatured"
                    onChange={change}
                    label={i18n.t("Feature on Homepage", {
                      context: "button"
                    })}
                  />
                </VisibilityCard>
              </div>
            </div>
          </Grid>
          <SaveButtonBar
            state={saveButtonBarState}
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onCollectionRemove}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  );
};
CollectionDetailsPage.displayName = "CollectionDetailsPage";
export default CollectionDetailsPage;
