import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputLabel } from "material-ui/Input";
import * as React from "react";

interface RichTextEditorProps {
  defaultValue?: string;
  error?: boolean;
  fullWidth?: boolean;
  helperText: string;
  label: string;
  name: string;
  value?: string;
  onChange(event: any);
}

export const RichTextEditor: React.StatelessComponent<RichTextEditorProps> = ({
  defaultValue,
  error,
  fullWidth,
  helperText,
  label,
  name,
  onChange,
  value
}) => (
  <FormControl style={fullWidth ? { width: "100%" } : {}} error={error}>
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
