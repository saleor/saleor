import "medium-editor/src/sass/medium-editor.scss";
import "medium-editor/src/sass/themes/default.scss";

import * as React from "react";
import Editor from "react-medium-editor";
import { withStyles } from "material-ui/styles";
import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputLabel } from "material-ui/Input";

interface RichTextEditorProps {
  label: string;
  helperText: string;
  value?: string;
  defaultValue?: string;
  name: string;
  fullWidth?: boolean;
  onChange(event: any);
}

export const RichTextEditor: React.StatelessComponent<RichTextEditorProps> = ({
  label,
  helperText,
  value,
  onChange,
  fullWidth,
  name,
  defaultValue
}) => (
  <FormControl style={fullWidth ? { width: "100%" } : {}}>
    <InputLabel shrink={!!(value || defaultValue)}>{label}</InputLabel>
    <Input
      multiline
      name={name}
      {...(value ? { value } : {})}
      {...(defaultValue ? { defaultValue } : {})}
      onChange={onChange}
      fullWidth={fullWidth}
    />
    <FormHelperText>{helperText}</FormHelperText>
  </FormControl>
);

export default RichTextEditor;
