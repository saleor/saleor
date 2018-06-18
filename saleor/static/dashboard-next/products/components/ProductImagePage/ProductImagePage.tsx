import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

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
                  rows={5}
                  multiline
                  fullWidth
                />
              </CardContent>
            </Card>
            <SaveButtonBar
              state={loading ? "disabled" : "default"}
              onSave={submit}
            />
          </>
        )}
      </Form>
    </Container>
  )
);
export default ProductImagePage;
