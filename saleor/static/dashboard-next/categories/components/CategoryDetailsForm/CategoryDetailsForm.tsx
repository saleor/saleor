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
import { CategoryDetails_category } from "../../types/CategoryDetails";

const styles = createStyles({
  root: {
    width: "50%"
  }
});

interface CategoryDetailsFormProps extends WithStyles<typeof styles> {
  category?: CategoryDetails_category;
  data: {
    name: string;
    description: RawDraftContentState;
  };
  disabled: boolean;
  errors: { [key: string]: string };
  onChange: (event: React.ChangeEvent<any>) => void;
}

export const CategoryDetailsForm = withStyles(styles, {
  name: "CategoryDetailsForm"
})(
  ({
    category,
    classes,
    disabled,
    data,
    onChange,
    errors
  }: CategoryDetailsFormProps) => {
    return (
      <Card>
        <CardTitle title={i18n.t("General information")} />
        <CardContent>
          <>
            <div>
              <TextField
                classes={{ root: classes.root }}
                label={i18n.t("Name")}
                name="name"
                disabled={disabled}
                value={data && data.name}
                onChange={onChange}
                error={!!errors.name}
                helperText={errors.name}
              />
            </div>
            <FormSpacer />
            <RichTextEditor
              disabled={disabled}
              error={!!errors.descriptionJson}
              helperText={errors.descriptionJson}
              label={i18n.t("Description")}
              initial={maybe(() => JSON.parse(category.descriptionJson))}
              name="description"
              onChange={onChange}
            />
          </>
        </CardContent>
      </Card>
    );
  }
);
CategoryDetailsForm.displayName = "CategoryDetailsForm";
export default CategoryDetailsForm;
