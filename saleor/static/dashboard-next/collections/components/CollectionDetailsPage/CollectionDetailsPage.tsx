import { withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import SeoForm from "../../../components/SeoForm/SeoForm";
import CollectionDetails from "../CollectionDetails";
import CollectionProducts from "../CollectionProducts";
import CollectionProperties from "../CollectionProperties";

interface CollectionDetailsPageProps {
  collection?: {
    id: string;
    name: string;
    slug: string;
    isPublished: boolean;
    backgroundImage: string;
    seoDescription?: string;
    seoTitle?: string;
  };
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
  storefrontUrl?(slug: string): string;
  onBack?();
  onCollectionDelete?();
  onCollectionShow?();
  onNextPage?();
  onPreviousPage?();
  onProductAdd?();
  onProductClick?(id: string): () => void;
  onProductRemove?(id: string): () => void;
  onSeoClick?(slug: string): () => void;
  onSubmit?();
}
interface CollectionDetailsPageState {
  backgroundImage: any;
  isPublished: boolean;
  name: string;
  slug: string;
  seoTitle: string;
  seoDescription: string;
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "3fr 2fr"
  }
}));
const CollectionDetailsPage = decorate<CollectionDetailsPageProps>(
  class CollectionDetailsPageComponent extends React.Component<
    CollectionDetailsPageProps & WithStyles<"root">,
    CollectionDetailsPageState
  > {
    constructor(props) {
      super(props);
      const { collection } = props;
      this.state = {
        backgroundImage: "",
        isPublished: collection ? collection.isPublished : false,
        name: collection ? collection.name : "",
        seoDescription: collection ? collection.seoDescription : "",
        seoTitle: collection ? collection.seoTitle : "",
        slug: collection ? collection.slug : ""
      };
    }

    onChange = (event: React.ChangeEvent<any>) => {
      this.setState({ [event.target.name]: event.target.value } as any);
    };

    render() {
      const {
        classes,
        collection,
        disabled,
        pageInfo,
        products,
        storefrontUrl,
        onBack,
        onCollectionDelete,
        onCollectionShow,
        onNextPage,
        onPreviousPage,
        onProductAdd,
        onProductClick,
        onProductRemove,
        onSeoClick,
        onSubmit
      } = this.props;
      return (
        <Container width="md">
          <PageHeader
            title={collection ? collection.name : undefined}
            onBack={onBack}
          />
          <div className={classes.root}>
            <div>
              <CollectionDetails
                collection={collection}
                onDelete={onCollectionDelete}
                disabled={disabled}
                data={this.state}
                onChange={this.onChange}
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
            </div>
            <div>
              <CollectionProperties
                collection={collection}
                data={this.state}
                onChange={this.onChange}
                disabled={disabled}
              />
              <SeoForm
                description={this.state.seoDescription}
                descriptionPlaceholder={
                  collection ? collection.seoDescription : ""
                }
                onChange={this.onChange}
                onClick={
                  !!onSeoClick ? onSeoClick(this.state.seoTitle) : undefined
                }
                storefrontUrl={storefrontUrl(this.state.slug)}
                title={this.state.seoTitle}
                titlePlaceholder={this.state.name}
              />
            </div>
          </div>
          <SaveButtonBar onBack={onBack} onSave={onSubmit} />
        </Container>
      );
    }
  }
);
CollectionDetailsPage.displayName = "CollectionDetailsPage";
export default CollectionDetailsPage;
