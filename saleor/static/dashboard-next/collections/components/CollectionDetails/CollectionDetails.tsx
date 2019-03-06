import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import { RawDraftContentState } from "draft-js";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { FormErrors } from "../../../types";
import { CollectionDetails_collection } from "../../types/CollectionDetails";

const styles = createStyles({
  name: {
    width: "80%"
  }
});

export interface CollectionDetailsProps extends WithStyles<typeof styles> {
  collection?: CollectionDetails_collection;
  data: {
    description: RawDraftContentState;
    name: string;
  };
  disabled: boolean;
  errors: FormErrors<"descriptionJson" | "name">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const CollectionDetails = withStyles(styles, { name: "CollectionDetails" })(
  ({
    classes,
    collection,
    disabled,
    data,
    onChange,
    errors
  }: CollectionDetailsProps) => (
    <Card>
      <CardTitle title={i18n.t("General information")} />
      <CardContent>
        <TextField
          classes={{ root: classes.name }}
          label={i18n.t("Name")}
          name="name"
          disabled={disabled}
          value={data.name}
          onChange={onChange}
          error={!!errors.name}
          helperText={errors.name}
        />
        <FormSpacer />
        <RichTextEditor
          error={!!errors.descriptionJson}
          helperText={errors.descriptionJson}
          initial={maybe(() => JSON.parse(collection.descriptionJson))}
          label={i18n.t("Description")}
          name="description"
          disabled={disabled}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
CollectionDetails.displayName = "CollectionDetails";
export default CollectionDetails;
