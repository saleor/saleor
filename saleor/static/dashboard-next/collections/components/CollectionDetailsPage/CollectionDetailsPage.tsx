import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import { CardSpacer } from "../../../components/CardSpacer";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import { maybe } from "../../../misc";
import { CollectionDetails_collection } from "../../types/CollectionDetails";
import CollectionDetails from "../CollectionDetails/CollectionDetails";

export interface CollectionDetailsPageFormData {
  name: string;
  seoDescription: string;
  seoTitle: string;
  isPublished: boolean;
}

export interface CollectionDetailsPageProps {
  collection: CollectionDetails_collection;
  disabled: boolean;
  onBack: () => void;
  onCollectionRemove: () => void;
  onImageUpload: () => void;
  onSubmit: (data: CollectionDetailsPageFormData) => void;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "9fr 4fr"
  }
}));
const CollectionDetailsPage = decorate<CollectionDetailsPageProps>(
  ({ classes, collection, disabled, onBack, onCollectionRemove, onSubmit }) => (
    <Form
      initial={{
        isPublished: maybe(() => collection.isPublished),
        name: maybe(() => collection.name),
        seoDescription: maybe(() => collection.seoDescription),
        seoTitle: maybe(() => collection.seoTitle)
      }}
      onSubmit={onSubmit}
    >
      {({ change, data, errors: formErrors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => collection.name)} onBack={onBack} />
          <div className={classes.root}>
            <div>
              <CollectionDetails
                data={data}
                disabled={disabled}
                errors={formErrors}
                onChange={change}
              />
              <CardSpacer />
              <CollectionProducts
                products={maybe(() =>
                  collection.products.edges.map(edge => edge.node)
                )}
              />
            </div>
            <div />
          </div>
          <SaveButtonBar
            disabled={disabled || !hasChanged}
            onCancel={onBack}
            onDelete={onCollectionRemove}
            onSave={submit}
          />
        </Container>
      )}
    </Form>
  )
);
CollectionDetailsPage.displayName = "CollectionDetailsPage";
export default CollectionDetailsPage;
