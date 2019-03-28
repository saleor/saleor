import Typography from "@material-ui/core/Typography";
import * as React from "react";

import DraftRenderer from "../../../components/DraftRenderer";
import Form from "../../../components/Form";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";
import TranslationFieldsSave from "./TranslationFieldsSave";

interface TranslationFieldsRichProps {
  disabled: boolean;
  edit: boolean;
  initial: string;
  onSubmit: (data: string) => void;
}

const TranslationFieldsRich: React.FC<TranslationFieldsRichProps> = ({
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
      {({ change, reset, submit }) => (
        <div>
          <RichTextEditor
            disabled={disabled}
            error={undefined}
            helperText={undefined}
            initial={JSON.parse(initial)}
            // label={i18n.t("Translation")}
            label={undefined}
            name="translation"
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
    <DraftRenderer content={JSON.parse(initial)} />
  );
TranslationFieldsRich.displayName = "TranslationFieldsRich";
export default TranslationFieldsRich;
