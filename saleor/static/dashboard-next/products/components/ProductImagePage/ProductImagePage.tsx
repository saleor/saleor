import Card, { CardContent, CardMedia } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import TextField from "material-ui/TextField";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductImagePageProps {
  image?: string;
  description?: string;
  loading?: boolean;
  onSubmit();
  onBack();
}

const decorate = withStyles(theme => ({
  root: {},
  image: {
    display: "block",
    marginLeft: "auto",
    marginRight: "auto",
    marginBottom: theme.spacing.unit * 2
  }
}));
const ProductImagePage = decorate<ProductImagePageProps>(
  ({ classes, image, description, loading, onSubmit, onBack }) => (
    <Container width="sm">
      <Form initial={{ description }} onSubmit={onSubmit}>
        {({ change, data, submit }) => (
          <>
            <PageHeader title={i18n.t("Edit image")} onBack={onBack} />
            <Card>
              <CardContent>
                {loading ? (
                  <Skeleton />
                ) : (
                  <img src={image} className={classes.image} />
                )}
                <TextField
                  name="description"
                  label={i18n.t("Description")}
                  helperText={i18n.t("Optional")}
                  disabled={loading}
                  multiline
                  fullWidth
                />
              </CardContent>
            </Card>
            <SaveButtonBar onBack={onBack} onSave={submit} />
          </>
        )}
      </Form>
    </Container>
  )
);
export default ProductImagePage;
