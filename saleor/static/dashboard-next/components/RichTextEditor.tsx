import { FormControl, FormHelperText } from "material-ui/Form";
import Input, { InputLabel } from "material-ui/Input";
import * as React from "react";

interface RichTextEditorProps {
  defaultValue?: string;
  disabled?: boolean;
  error?: boolean;
  fullWidth?: boolean;
  helperText: string;
  label?: string;
  name: string;
  value?: string;
  onChange(event: any);
}

export const RichTextEditor: React.StatelessComponent<RichTextEditorProps> = ({
  defaultValue,
  disabled,
  error,
  fullWidth,
  helperText,
  label,
  name,
  onChange,
  value
}) => (
  <FormControl style={fullWidth ? { width: "100%" } : {}} error={error}>
    {label && (
      <InputLabel shrink={!!(value || defaultValue)}>{label}</InputLabel>
    )}
    <Input
      disabled={disabled}
      multiline
      name={name}
      {...(value ? { value } : {})}
      {...(defaultValue ? { defaultValue } : {})}
      onChange={onChange}
      fullWidth={fullWidth}
    />
    {helperText && <FormHelperText>{helperText}</FormHelperText>}
  </FormControl>
);

export default RichTextEditor;
