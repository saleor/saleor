import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { ListProps } from "../../..";
import CardTitle from "../../../components/CardTitle";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import ProductImageNavigation from "../ProductImageNavigation";

interface ProductImagePageProps extends ListProps {
  image?: {
    id: string;
    url: string;
  };
  images?: Array<{
    id: string;
    url: string;
  }>;
  description?: string;
  saveButtonBarState?: SaveButtonBarState;
  onBack: () => void;
  onDelete: () => void;
  onSubmit: (data: { description: string }) => void;
}

const decorate = withStyles(theme => ({
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    width: "100%"
  },
  imageContainer: {
    background: "#ffffff",
    border: "1px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    margin: `0 auto ${theme.spacing.unit * 2}px`,
    maxWidth: 552,
    padding: theme.spacing.unit * 2
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "4fr 9fr"
  }
}));
const ProductImagePage = decorate<ProductImagePageProps>(
  ({
    classes,
    description,
    disabled,
    image,
    images,
    pageInfo,
    saveButtonBarState,
    onBack,
    onDelete,
    onNextPage,
    onPreviousPage,
    onRowClick,
    onSubmit
  }) => (
    <Form
      initial={{ description: description || "" }}
      onSubmit={onSubmit}
      key={description}
    >
      {({ change, data, hasChanged, submit }) => {
        return (
          <Container width="md">
            <PageHeader title={i18n.t("Edit Photo")} onBack={onBack} />
            <div className={classes.root}>
              <div>
                <ProductImageNavigation
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  disabled={disabled}
                  images={images}
                  highlighted={image ? image.id : undefined}
                  onRowClick={onRowClick}
                  pageInfo={pageInfo}
                />
                <Card>
                  <CardTitle title={i18n.t("Photo Information")} />
                  <CardContent>
                    <TextField
                      name="description"
                      label={i18n.t("Description")}
                      helperText={i18n.t("Optional")}
                      disabled={disabled}
                      onChange={change}
                      value={data.description}
                      multiline
                      fullWidth
                    />
                  </CardContent>
                </Card>
              </div>
              <div>
                <Card>
                  <CardTitle title={i18n.t("Photo View")} />
                  <CardContent>
                    {!!image ? (
                      <div className={classes.imageContainer}>
                        <img src={image.url} className={classes.image} />
                      </div>
                    ) : (
                      <Skeleton />
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
            <SaveButtonBar
              disabled={disabled || !onSubmit || !hasChanged}
              state={saveButtonBarState}
              onDelete={onDelete}
              onSave={submit}
            />
          </Container>
        );
      }}
    </Form>
  )
);
export default ProductImagePage;
