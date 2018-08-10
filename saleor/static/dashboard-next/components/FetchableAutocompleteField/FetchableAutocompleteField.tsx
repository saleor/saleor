import * as React from "react";
import SingleAutocompleteField from "../SingleAutocompleteField";

interface FetchableAutocompleteFieldProps {
  choices: Array<{
    label?: React.ReactNode;
    name: string;
    value: string;
  }>;
  custom?: boolean;
  disabled?: boolean;
  helperText?: string;
  label?: string;
  loading: boolean;
  name: string;
  placeholder?: string;
  value: string;
  onChange: (event: React.ChangeEvent<any>) => void;
  fetchChoices?: (value: string) => void;
}

const FetchableAutocompleteField: React.StatelessComponent<
  FetchableAutocompleteFieldProps
> = ({ fetchChoices, ...other }) => {
  return (
    <SingleAutocompleteField
      sort={false}
      onInputChange={fetchChoices}
      {...other}
    />
  );
};
FetchableAutocompleteField.displayName = "FetchableAutocompleteField";
export default FetchableAutocompleteField;
