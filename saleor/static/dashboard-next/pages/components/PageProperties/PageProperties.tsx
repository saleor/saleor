import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ControlledCheckbox from "../../../components/ControlledCheckbox";
import DateFormatter from "../../../components/DateFormatter";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";

interface PagePropertiesProps {
  publicationDate: string;
  created?: string;
  errors?: Array<{ field: string; message: string }>;
  isPublished: boolean;
  loading?: boolean;
  slug?: string;
  onChange?(event: React.ChangeEvent<any>);
}

const PageProperties: React.StatelessComponent<PagePropertiesProps> = ({
  created,
  errors,
  slug,
  publicationDate,
  loading,
  isPublished,
  onChange
}) => {
  const errorList: { [key: string]: string } = errors
    ? errors.reduce((acc, curr) => {
        acc[curr.field] = curr.message;
        return acc;
      }, {})
    : {};
  return (
    <Card>
      <CardContent>
        <TextField
          disabled={loading}
          name="slug"
          label={i18n.t("Slug", { context: "object" })}
          value={slug}
          helperText={
            errorList && errorList.slug
              ? errorList.slug
              : i18n.t("Slug is being used to create page URL", {
                  context: "object"
                })
          }
          onChange={onChange}
          error={!!(errorList && errorList.slug)}
          fullWidth
        />
        <FormSpacer />
        <TextField
          disabled={loading}
          name="publicationDate"
          label={i18n.t("Publication date", { context: "label" })}
          type="date"
          value={publicationDate}
          onChange={onChange}
          InputLabelProps={{
            shrink: true
          }}
          helperText={
            errorList && errorList.publicationDate ? errorList.publicationDate : ""
          }
          error={!!(errorList && errorList.publicationDate)}
          fullWidth
        />
        <FormSpacer />
        {created && (
          <div>
            <Typography variant="body1">
              {i18n.t("Created:")} <DateFormatter date={created} />
            </Typography>
          </div>
        )}
        <FormSpacer />
        <ControlledCheckbox
          checked={isPublished}
          disabled={loading}
          label={i18n.t("Published", { context: "label" })}
          name="isPublished"
          onChange={onChange}
        />
      </CardContent>
    </Card>
  );
};
PageProperties.displayName = "PageProperties";
export default PageProperties;
