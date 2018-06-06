import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";

interface PageContentProps {
  content: string;
  errors?: Array<{ field: string; message: string }>;
  loading?: boolean;
  title: string;
  onChange?(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  addHelperTextPadding: {
    [theme.breakpoints.up("md")]: {
      paddingBottom: theme.spacing.unit * 2.5
    }
  }
}));
const PageContent = decorate<PageContentProps>(
  ({ classes, content, errors, loading, title, onChange }) => {
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
            autoFocus
            disabled={loading}
            name="title"
            label={i18n.t("Title", { context: "object" })}
            value={title}
            onChange={onChange}
            className={
              (errors
              ? !errorList.title
              : true)
                ? classes.addHelperTextPadding
                : ""
            }
            error={!!(errorList && errorList.title)}
            helperText={errorList && errorList.title ? errorList.title : ""}
            fullWidth
          />
          <FormSpacer />
          <RichTextEditor
            disabled={loading}
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
        </CardContent>
      </Card>
    );
  }
);
export default PageContent;
