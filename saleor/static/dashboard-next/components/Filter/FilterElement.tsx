import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/styles";
import * as React from "react";

import i18n from "../../i18n";
import Calendar from "../../icons/Calendar";
import FormSpacer from "../FormSpacer";
import SingleSelectField from "../SingleSelectField";
import { FieldType, IFilterItem } from "./types";

export interface FilterElementProps {
  className?: string;
  filter: IFilterItem;
  value: string | string[];
  onChange: (value: string | string[]) => void;
}

const useStyles = makeStyles({
  calendar: {
    margin: 8
  },
  input: {
    padding: "20px 12px 17px"
  }
});

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
  const classes = useStyles();

  if (filter.data.type === FieldType.date) {
    return (
      <TextField
        className={className}
        fullWidth
        type="date"
        onChange={event => onChange(event.target.value)}
        value={value}
        InputProps={{
          classes: {
            input: classes.input
          },
          startAdornment: <Calendar className={classes.calendar} />
        }}
      />
    );
  } else if (filter.data.type === FieldType.rangeDate) {
    return (
      <>
        <Typography>{i18n.t("from")}</Typography>
        <TextField
          className={className}
          fullWidth
          type="date"
          value={value[0]}
          onChange={event => onChange([event.target.value, value[1]])}
          InputProps={{
            startAdornment: <Calendar className={classes.calendar} />
          }}
        />
        <FormSpacer />
        <Typography>{i18n.t("to")}</Typography>
        <TextField
          className={className}
          fullWidth
          type="date"
          value={value[1]}
          onChange={event => onChange([value[0], event.target.value])}
          InputProps={{
            startAdornment: <Calendar className={classes.calendar} />
          }}
        />
      </>
    );
  } else if (filter.data.type === FieldType.range) {
    return (
      <>
        <Typography>{i18n.t("from")}</Typography>
        <TextField
          className={className}
          fullWidth
          value={value[0]}
          onChange={event => onChange([event.target.value, value[1]])}
          type="number"
        />
        <FormSpacer />
        <Typography>{i18n.t("to")}</Typography>
        <TextField
          className={className}
          fullWidth
          value={value[1]}
          onChange={event => onChange([value[0], event.target.value])}
          type="number"
        />
      </>
    );
  } else if (filter.data.type === FieldType.select) {
    return (
      <SingleSelectField
        choices={filter.data.options.map(option => ({
          ...option,
          value: option.value.toString()
        }))}
        value={value as string}
        placeholder={i18n.t("Select Filter...")}
        onChange={event => onChange(event.target.value)}
      />
    );
  }
  return <TextField className={className} fullWidth label={filter.label} />;
};
FilterElement.displayName = "FilterElement";
export default FilterElement;
