import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import { RichTextEditor } from "../../../components/RichTextEditor";

import i18n from "../../../i18n";

interface CategoryDetailsFormProps {
  data: {
    name: string;
    description: string;
  };
  disabled: boolean;
  errors: { [key: string]: string };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({
  root: {
    width: "50%"
  }
});

export const CategoryDetailsForm = decorate<CategoryDetailsFormProps>(
  ({ classes, disabled, data, onChange, errors }) => {
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
              label={i18n.t("Description")}
              fullWidth
              helperText={
                errors.description
                  ? errors.description
                  : i18n.t("Select text to enable text-formatting tools.")
              }
              name="description"
              value={data.description}
              onChange={onChange}
              error={!!errors.description}
            />
          </>
        </CardContent>
      </Card>
    );
  }
);
export default CategoryDetailsForm;
