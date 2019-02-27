import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { FormErrors } from "../../../types";
import { PageDetails_page } from "../../types/PageDetails";
import { FormData } from "../PageDetailsPage";

export interface PageInfoProps {
  data: FormData;
  disabled: boolean;
  errors: FormErrors<"contentJson" | "title">;
  page: PageDetails_page;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = createStyles({
  root: {
    overflow: "visible"
  }
});

const PageInfo = withStyles(styles, {
  name: "PageInfo"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    page,
    onChange
  }: PageInfoProps & WithStyles<typeof styles>) => (
    <Card className={classes.root}>
      <CardTitle title={i18n.t("General Informations")} />
      <CardContent>
        <TextField
          disabled={disabled}
          error={!!errors.title}
          fullWidth
          helperText={errors.title}
          label={i18n.t("Title")}
          name={"title" as keyof FormData}
          value={data.title}
          onChange={onChange}
        />
        <FormSpacer />
        <RichTextEditor
          disabled={disabled}
          error={!!errors.contentJson}
          helperText={errors.contentJson}
          initial={maybe(() => JSON.parse(page.contentJson))}
          label={i18n.t("Content")}
          name={"content" as keyof FormData}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
PageInfo.displayName = "PageInfo";
export default PageInfo;
