import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { FormData } from "../PageDetailsPage";

export interface PageInfoProps {
  data: FormData;
  disabled: boolean;
  errors: Partial<Record<"title" | "content", string>>;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const PageInfo: React.StatelessComponent<PageInfoProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <Card>
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
      <TextField
        disabled={disabled}
        error={!!errors.title}
        fullWidth
        helperText={errors.title}
        label={i18n.t("Content")}
        name={"title" as keyof FormData}
        value={data.content}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
PageInfo.displayName = "PageInfo";
export default PageInfo;
