import MenuItem from "@material-ui/core/MenuItem";
import Select from "@material-ui/core/Select";
import { Theme } from "@material-ui/core/styles";
import { createStyles, makeStyles, useTheme } from "@material-ui/styles";
import React from "react";

import i18n from "../../i18n";
import { ListSettings } from "../../types";

const useStyles = makeStyles(
  (theme: Theme) =>
    createStyles({
      label: {
        fontSize: 14
      },
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
    }),
  {
    name: "RowNumberSelect"
  }
);

interface RowNumberSelectProps {
  choices: number[];
  className?: string;
  settings: ListSettings;
  onChange(key: keyof ListSettings, value: any);
}

const RowNumberSelect: React.FC<RowNumberSelectProps> = ({
  className,
  choices,
  settings,
  onChange
}) => {
  const theme = useTheme();
  const classes = useStyles({ theme });
  return (
    <div className={className}>
      <span className={classes.label}>{i18n.t("No of Rows:")}</span>
      <Select
        className={classes.select}
        value={settings.rowNumber}
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
};

export default RowNumberSelect;
