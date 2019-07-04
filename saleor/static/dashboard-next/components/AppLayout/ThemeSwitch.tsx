import { Theme, withStyles } from "@material-ui/core/styles";
import Switch, { SwitchProps } from "@material-ui/core/Switch";
import React from "react";

import MoonIcon from "../../icons/Moon";
import SunIcon from "../../icons/Sun";

const switchStyles = (theme: Theme) => ({
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
  root: {
    "& svg": {
      background: theme.palette.primary.main,
      borderRadius: "100%",
      height: 20,
      width: 20
    },
    width: 58
  }
});
const ThemeSwitch = withStyles(switchStyles, {
  name: "ThemeSwitch"
})((props: SwitchProps) => (
  <Switch
    {...props}
    color="primary"
    icon={<SunIcon />}
    checkedIcon={<MoonIcon />}
  />
));
ThemeSwitch.displayName = "ThemeSwitch";
export default ThemeSwitch;
