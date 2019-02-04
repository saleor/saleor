import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";

export interface CustomerCreateNoteProps {
  data: {
    note: string;
  };
  disabled: boolean;
  errors: Partial<{
    note: string;
  }>;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const CustomerCreateNote: React.StatelessComponent<CustomerCreateNoteProps> = ({
  data,
  disabled,
  errors,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("Notes")} />
    <CardContent>
      <Typography>
        {i18n.t("Enter any extra infotmation regarding this customer.")}
      </Typography>
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.note}
        fullWidth
        multiline
        name="note"
        helperText={errors.note}
        label={i18n.t("Note")}
        value={data.note}
        onChange={onChange}
      />
    </CardContent>
  </Card>
);
CustomerCreateNote.displayName = "CustomerCreateNote";
export default CustomerCreateNote;
