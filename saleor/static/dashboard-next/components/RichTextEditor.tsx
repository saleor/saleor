import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import Input, { InputClassKey } from "@material-ui/core/Input";
import InputLabel from "@material-ui/core/InputLabel";
import * as React from "react";

interface RichTextEditorProps {
  classes?: Partial<Record<InputClassKey, string>>;
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
  classes,
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
    {label && <InputLabel shrink={!!value}>{label}</InputLabel>}
    <Input
      classes={classes}
      disabled={disabled}
      multiline
      name={name}
      value={value}
      onChange={onChange}
      fullWidth={fullWidth}
    />
    {helperText && <FormHelperText>{helperText}</FormHelperText>}
  </FormControl>
);

RichTextEditor.displayName = "RichTextEditor";
export default RichTextEditor;
