import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import SeoForm from "../../../components/SeoForm";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import CollectionDetails from "../CollectionDetails";
import CollectionProducts from "../CollectionProducts";
import CollectionProperties from "../CollectionProperties";

interface CollectionForm {
  name: string;
  slug: string;
  isPublished: boolean;
  backgroundImage: string;
  seoDescription?: string;
  seoTitle?: string;
}
interface CollectionDetailsPageProps {
  collection?: CollectionForm;
  disabled?: boolean;
  products?: Array<{
    id: string;
    name: string;
    sku: string;
    availability: {
      available: boolean;
    };
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  saveButtonBarState?: SaveButtonBarState;
  storefrontUrl: (slug: string) => string;
  onBack: () => void;
  onDelete: () => void;
  onImageRemove: () => void;
  onNextPage: () => void;
  onPreviousPage: () => void;
  onProductAdd: () => void;
  onProductClick: (id: string) => () => void;
  onProductRemove: (id: string) => () => void;
  onSeoClick?: (slug: string) => () => void;
  onShow: () => void;
  onSubmit: (data: CollectionForm) => void;
}

const decorate = withStyles(theme => ({
  cardSpacer: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginTop: theme.spacing.unit
    }
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "3fr 2fr"
  }
}));
const CollectionDetailsPage = decorate<CollectionDetailsPageProps>(
  ({
    classes,
    collection,
    disabled,
    pageInfo,
    products,
    saveButtonBarState,
    storefrontUrl,
    onBack,
    onDelete,
    onImageRemove,
    onNextPage,
    onPreviousPage,
    onProductAdd,
    onProductClick,
    onProductRemove,
    onSeoClick,
    onShow,
    onSubmit
  }) => (
    <Toggle>
      {(openedRemoveDialog, { toggle: toggleRemoveDialog }) => (
        <Toggle>
          {(openedImageRemoveDialog, { toggle: toggleImageRemoveDialog }) => (
            <>
              <Form
                initial={{
                  backgroundImage: "",
                  isPublished: collection ? collection.isPublished : false,
                  name: collection ? collection.name : "",
                  seoDescription: collection ? collection.seoDescription : "",
                  seoTitle: collection ? collection.seoTitle : "",
                  slug: collection ? collection.slug : ""
                }}
                onSubmit={onSubmit}
              >
                {({ change, data, hasChanged, submit }) => (
                  <Container width="md">
                    <PageHeader
                      title={collection ? collection.name : undefined}
                      onBack={onBack}
                    >
                      <Button
                        color="secondary"
                        variant="flat"
                        disabled={disabled}
                        onClick={onShow}
                      >
                        {i18n.t("Show on storefront")}
                      </Button>
                    </PageHeader>
                    <div className={classes.root}>
                      <div>
                        <CollectionDetails
                          collection={collection}
                          disabled={disabled}
                          data={data}
                          onChange={change}
                          onImageRemove={toggleImageRemoveDialog}
                        />
                        <CollectionProducts
                          products={products}
                          pageInfo={pageInfo}
                          disabled={disabled}
                          onNextPage={onNextPage}
                          onPreviousPage={onPreviousPage}
                          onProductAdd={onProductAdd}
                          onProductClick={onProductClick}
                          onProductRemove={onProductRemove}
                        />
                        <div className={classes.cardSpacer} />
                        <SeoForm
                          helperText={i18n.t(
                            "Add search engine title and description to make this collection easier to find"
                          )}
                          description={data.seoDescription}
                          descriptionPlaceholder={
                            collection && collection.seoDescription
                              ? collection.seoDescription
                              : i18n.t("No description provided")
                          }
                          onChange={change}
                          onClick={
                            !!onSeoClick ? onSeoClick(data.seoTitle) : undefined
                          }
                          storefrontUrl={storefrontUrl(data.slug)}
                          title={data.seoTitle}
                          titlePlaceholder={data.name}
                        />
                      </div>
                      <div>
                        <CollectionProperties
                          collection={collection}
                          data={data}
                          onChange={change}
                          disabled={disabled}
                        />
                      </div>
                    </div>
                    <SaveButtonBar
                      onCancel={onBack}
                      onDelete={toggleRemoveDialog}
                      onSave={submit}
                      disabled={disabled || !onSubmit || !hasChanged}
                      state={saveButtonBarState}
                    />
                  </Container>
                )}
              </Form>
              <ActionDialog
                onClose={toggleRemoveDialog}
                onConfirm={onDelete}
                open={openedRemoveDialog}
                title={i18n.t("Remove collection")}
                variant="delete"
              >
                <DialogContentText
                  dangerouslySetInnerHTML={{
                    __html: i18n.t(
                      "Are you sure you want to remove <strong>{{ name }}</strong>?",
                      { name: collection ? collection.name : undefined }
                    )
                  }}
                />
              </ActionDialog>
              <ActionDialog
                onClose={toggleImageRemoveDialog}
                onConfirm={onImageRemove}
                open={openedImageRemoveDialog}
                title={i18n.t("Remove image")}
                variant="delete"
              >
                <DialogContentText>
                  {i18n.t(
                    "Are you sure you want to remove collection's image?"
                  )}
                </DialogContentText>
              </ActionDialog>
            </>
          )}
        </Toggle>
      )}
    </Toggle>
  )
);
CollectionDetailsPage.displayName = "CollectionDetailsPage";
export default CollectionDetailsPage;
