import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ControlledCheckbox from "../../../components/ControlledCheckbox";
import FormSpacer from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface CollectionPropertiesProps {
  collection?: {
    isPublished: boolean;
    slug: string;
  };
  data: {
    isPublished: boolean;
    slug: string;
  };
  disabled?: boolean;
  onChange?(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  root: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: { marginBottom: theme.spacing.unit }
  }
}));
const CollectionProperties = decorate<CollectionPropertiesProps>(
  ({ classes, collection, data, disabled, onChange }) => (
    <Card className={classes.root}>
      <PageHeader title={i18n.t("Properties")} />
      <CardContent>
        <ControlledCheckbox
          checked={data.isPublished}
          disabled={disabled}
          label={i18n.t("Published")}
          name="isPublished"
          onChange={onChange}
        />
        <FormSpacer />
        <TextField
          disabled={disabled}
          fullWidth
          helperText={i18n.t("Slug is being used to create collection URL")}
          label={i18n.t("Slug")}
          name="slug"
          onChange={onChange}
          placeholder={collection ? collection.slug : ""}
          value={data.slug}
        />
      </CardContent>
    </Card>
  )
);
CollectionProperties.displayName = "CollectionProperties";
export default CollectionProperties;
