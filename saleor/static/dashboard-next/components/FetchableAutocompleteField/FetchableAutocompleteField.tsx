import CircularProgress from "@material-ui/core/CircularProgress";
import * as React from "react";

import ArrowDropdownIcon from "../../icons/ArrowDropdown";
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
  initialLabel?: string;
  name: string;
  placeholder?: string;
  value: string;
  onChange: (event: React.ChangeEvent<any>) => void;
  fetchChoices?: (value: string) => void;
}

const FetchableAutocompleteField: React.StatelessComponent<
  FetchableAutocompleteFieldProps
> = ({ fetchChoices, loading, ...other }) => {
  return (
    <SingleAutocompleteField
      sort={false}
      InputProps={{
        endAdornment: loading ? (
          <CircularProgress
            size={18}
            style={{ marginTop: 4, marginRight: 4 }}
          />
        ) : (
          <ArrowDropdownIcon />
        )
      }}
      onInputChange={fetchChoices}
      {...other}
    />
  );
};
FetchableAutocompleteField.displayName = "FetchableAutocompleteField";
export default FetchableAutocompleteField;
