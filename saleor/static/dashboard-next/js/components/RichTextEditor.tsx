import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputLabel } from "material-ui/Input";
import { withStyles } from "material-ui/styles";
import * as React from "react";

interface RichTextEditorProps {
  defaultValue?: string;
  fullWidth?: boolean;
  helperText: string;
  label: string;
  name: string;
  value?: string;
  onChange(event: any);
}

export const RichTextEditor: React.StatelessComponent<RichTextEditorProps> = ({
  defaultValue,
  fullWidth,
  helperText,
  label,
  name,
  onChange,
  value
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
