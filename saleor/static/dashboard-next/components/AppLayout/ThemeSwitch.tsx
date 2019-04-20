import { Theme, withStyles, WithStyles } from "@material-ui/core/styles";
import { CSSProperties } from "@material-ui/core/styles/withStyles";
import Switch, { SwitchClassKey, SwitchProps } from "@material-ui/core/Switch";
import * as React from "react";

import MoonIcon from "../../icons/Moon";
import SunIcon from "../../icons/Sun";

const switchStyles: (
  theme: Theme
) => Record<SwitchClassKey, CSSProperties> = theme => ({
  bar: {
    "$colorPrimary$checked + &": {
      backgroundColor: theme.palette.background.paper
    },
    background: theme.palette.background.paper
  },
  checked: {
    "& svg": {
      background: theme.palette.primary.main,
      color: theme.palette.background.paper
    }
  },
  colorPrimary: {},
  colorSecondary: {},
  disabled: {},
  icon: {},
  iconChecked: {},
  input: {},
  root: {
    "& svg": {
      background: theme.palette.primary.main,
      borderRadius: "100%",
      height: 20,
      width: 20
    },
    width: 58
  },
  switchBase: {}
});
const ThemeSwitch = withStyles(switchStyles, {
  name: "ThemeSwitch"
})((props: SwitchProps & WithStyles<typeof switchStyles>) => (
  <Switch
    {...props}
    color="primary"
    icon={<SunIcon />}
    checkedIcon={<MoonIcon />}
  />
));
ThemeSwitch.displayName = "ThemeSwitch";
export default ThemeSwitch;
