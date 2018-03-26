import Button from "material-ui/Button";
import { CardContent } from "material-ui/Card";
import Grid from "material-ui/Grid";
import { withStyles, WithStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import * as React from "react";

import ControlledCheckbox from "../../components/ControlledCheckbox";
import FormSpacer from "../../components/FormSpacer";
import RichTextEditor from "../../components/RichTextEditor";
import i18n from "../../i18n";

// FIXME: Change name
interface PageBaseFormComponentProps {
  availableOn: string;
  content: string;
  created?: string;
  errors?: Array<{ field: string; message: string }>;
  isVisible: boolean;
  slug: string;
  title: string;
  onChange?(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  addHelperTextPadding: {
    [theme.breakpoints.up("md")]: {
      paddingBottom: theme.spacing.unit * 2.5
    }
  },
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
}));

export const PageBaseForm = decorate<PageBaseFormComponentProps>(
  ({
    classes,
    created,
    errors,
    title,
    content,
    slug,
    availableOn,
    isVisible,
    onChange
  }) => {
    const errorList: { [key: string]: string } = errors.reduce((acc, curr) => {
      acc[curr.field] = curr.message;
      return acc;
    }, {});
    return (
      <CardContent>
        <Grid container spacing={16}>
          <Grid item xs={12} md={9}>
            <TextField
              autoFocus
              name="title"
              label={i18n.t("Title", { context: "object" })}
              value={title}
              onChange={onChange}
              className={
                (errors ? !errorList.title : true)
                  ? classes.addHelperTextPadding
                  : ""
              }
              error={!!(errorList && errorList.title)}
              helperText={errorList && errorList.title ? errorList.title : ""}
              fullWidth
            />
            <FormSpacer />
            <RichTextEditor
              value={content}
              name="content"
              label={i18n.t("Content", { context: "object" })}
              helperText={
                errorList && errorList.content
                  ? errorList.content
                  : i18n.t("Select text to enable text-formatting tools.", {
                      context: "object"
                    })
              }
              onChange={onChange}
              error={!!(errorList && errorList.content)}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
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
              name="availableOn"
              label={i18n.t("Available on", { context: "label" })}
              type="date"
              value={availableOn}
              onChange={onChange}
              InputLabelProps={{
                shrink: true
              }}
              helperText={
                errorList && errorList.availableOn ? errorList.availableOn : ""
              }
              error={!!(errorList && errorList.availableOn)}
            />
            <FormSpacer />
            {created && (
              <Typography variant="body1">Created at: {created}</Typography>
            )}
            <FormSpacer />
            <ControlledCheckbox
              checked={isVisible}
              label={i18n.t("Published", { context: "label" })}
              name="isVisible"
              onChange={onChange}
            />
          </Grid>
        </Grid>
      </CardContent>
    );
  }
);

export default PageBaseForm;
