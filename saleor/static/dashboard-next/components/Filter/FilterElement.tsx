import TextField from "@material-ui/core/TextField";
import * as React from "react";

import i18n from "../../i18n";
import FormSpacer from "../FormSpacer";
import SingleSelectField from "../SingleSelectField";
import { FieldType, IFilterItem } from "./types";

export interface FilterElementProps {
  className?: string;
  filter: IFilterItem;
  value: string | string[];
  onChange: (value: string | string[]) => void;
}

const FilterElement: React.FC<FilterElementProps> = ({
  className,
  filter,
  onChange,
  value
}) => {
  if (filter.data.type === FieldType.date) {
    return (
      <TextField
        className={className}
        fullWidth
        label={filter.label}
        type="date"
        onChange={event => onChange(event.target.value)}
        value={value}
      />
    );
  } else if (filter.data.type === FieldType.rangeDate) {
    return (
      <>
        <TextField
          className={className}
          fullWidth
          label={i18n.t("From")}
          type="date"
          value={value[0]}
          onChange={event => onChange([event.target.value, value[1]])}
        />
        <FormSpacer />
        <TextField
          className={className}
          fullWidth
          label={i18n.t("To")}
          type="date"
          value={value[1]}
          onChange={event => onChange([value[0], event.target.value])}
        />
      </>
    );
  } else if (filter.data.type === FieldType.select) {
    return (
      <SingleSelectField
        choices={filter.children.map(filterItem => ({
          label: filterItem.label,
          value: filterItem.value
        }))}
        onChange={event => onChange(event.target.value)}
      />
    );
  }
  return <TextField className={className} fullWidth label={filter.label} />;
};
FilterElement.displayName = "FilterElement";
export default FilterElement;
