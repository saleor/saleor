import MenuItem from "@material-ui/core/MenuItem";
import Select from "@material-ui/core/Select";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import classNames from "classnames";
import React from "react";

import i18n from "../../i18n";
import { ListSettings } from "../../types";

const styles = (theme: Theme) =>
  createStyles({
    label: {
      fontSize: "14px"
    },
    root: {},
    select: {
      "& div": {
        "&:focus": {
          background: "none"
        },
        color: theme.palette.primary.main,
        padding: "0 10px 0 5px"
      },
      "& svg": {
        color: theme.palette.primary.main
      },
      "&:after, &:before, &:hover": {
        border: "none !important"
      }
    }
  });

interface RowNumberSelectProps extends WithStyles<typeof styles> {
  choices: number[];
  className?: string;
  listSettings: ListSettings;
  onChange(key: keyof ListSettings, value: any);
}

const RowNumberSelect = withStyles(styles, { name: "RowNumberSelect" })(
  ({
    classes,
    className,
    choices,
    listSettings,
    onChange
  }: RowNumberSelectProps) => {
    return (
      <div className={classNames(classes.root, className)}>
        <span className={classes.label}>{i18n.t("No of Rows:")}</span>
        <Select
          className={classes.select}
          value={listSettings.rowNumber}
          onChange={event => onChange("rowNumber", event.target.value)}
        >
          {choices.length > 0 &&
            choices.map(choice => (
              <MenuItem value={choice} key={choice}>
                {choice}
              </MenuItem>
            ))}
        </Select>
      </div>
    );
  }
);

RowNumberSelect.displayName = "RowNumberSelect";
export default RowNumberSelect;
