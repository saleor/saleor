import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar, {
  SaveButtonBarState
} from "../../../components/SaveButtonBar";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductImagePageProps {
  image?: string;
  description?: string;
  disabled?: boolean;
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
    gridTemplateColumns: "1fr 2.25fr"
  }
}));
const ProductImagePage = decorate<ProductImagePageProps>(
  ({
    classes,
    image,
    description,
    disabled,
    saveButtonBarState,
    onBack,
    onDelete,
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
                        <img src={image} className={classes.image} />
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
