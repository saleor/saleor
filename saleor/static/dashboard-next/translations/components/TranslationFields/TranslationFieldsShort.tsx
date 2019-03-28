import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Form from "../../../components/Form";
import i18n from "../../../i18n";
import TranslationFieldsSave from "./TranslationFieldsSave";

interface TranslationFieldsShortProps {
  disabled: boolean;
  edit: boolean;
  initial: string;
  onSubmit: (data: string) => void;
}

const TranslationFieldsShort: React.FC<TranslationFieldsShortProps> = ({
  disabled,
  edit,
  initial,
  onSubmit
}) =>
  edit ? (
    <Form
      initial={{ translation: initial }}
      onSubmit={data => onSubmit(data.translation)}
    >
      {({ change, data, reset, submit }) => (
        <div>
          <TextField
            disabled={disabled}
            fullWidth
            // label={i18n.t("Translation")}
            name="translation"
            value={data.translation}
            onChange={change}
          />
          <TranslationFieldsSave onDiscard={reset} onSave={submit} />
        </div>
      )}
    </Form>
  ) : initial === null ? (
    <Typography color="textSecondary">
      {i18n.t("No translation yet")}
    </Typography>
  ) : (
    initial
  );
TranslationFieldsShort.displayName = "TranslationFieldsShort";
export default TranslationFieldsShort;
