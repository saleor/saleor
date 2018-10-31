import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as classNames from "classnames";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";

interface PageContentProps {
  content: string;
  errors: {
    content?: string;
    title?: string;
  };
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
  ({ classes, content, errors, loading, title, onChange }) => (
    <Card>
      <CardContent>
        <TextField
          autoFocus
          disabled={loading}
          name="title"
          label={i18n.t("Title", { context: "object" })}
          value={title}
          onChange={onChange}
          className={classNames({
            [classes.addHelperTextPadding]: !errors.title
          })}
          error={!!errors.title}
          helperText={errors.title ? errors.title : undefined}
          fullWidth
        />
        <FormSpacer />
        <RichTextEditor
          disabled={loading}
          value={content}
          name="content"
          label={i18n.t("Content", { context: "object" })}
          helperText={
            errors.content
              ? errors.content
              : i18n.t("Select text to enable text-formatting tools.", {
                  context: "object"
                })
          }
          onChange={onChange}
          error={!!errors.content}
          fullWidth
        />
      </CardContent>
    </Card>
  )
);
PageContent.displayName = "PageContent";
export default PageContent;
