import Card from "@material-ui/core/Card";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import ArrowDropDown from "@material-ui/icons/ArrowDropDown";
import classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";
import { LanguageCodeEnum } from "../../types/globalTypes";
import { ShopInfo_shop_languages } from "../Shop/types/ShopInfo";

export interface LanguageSwitchProps {
  currentLanguage: LanguageCodeEnum;
  languages: ShopInfo_shop_languages[];
  onLanguageChange: (lang: LanguageCodeEnum) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    arrow: {
      color: theme.palette.primary.main,
      transition: theme.transitions.duration.standard + "ms"
    },
    container: {
      paddingBottom: theme.spacing.unit
    },
    menuContainer: {
      cursor: "pointer",
      display: "flex",
      justifyContent: "space-between",
      minWidth: 90,
      padding: theme.spacing.unit,
      position: "relative"
    },
    menuItem: {
      textAlign: "justify"
    },
    menuPaper: {
      maxHeight: `calc(100vh - ${theme.spacing.unit * 2}px)`,
      overflow: "scroll"
    },
    popover: {
      zIndex: 1
    },
    rotate: {
      transform: "rotate(180deg)"
    }
  });
const LanguageSwitch = withStyles(styles, { name: "LanguageSwitch" })(
  ({
    classes,
    currentLanguage,
    languages,
    onLanguageChange
  }: LanguageSwitchProps & WithStyles<typeof styles>) => {
    const [isExpanded, setExpandedState] = React.useState(false);
    const anchor = React.useRef();

    return (
      <div className={classes.container} ref={anchor}>
        <Card
          className={classes.menuContainer}
          onClick={() => setExpandedState(!isExpanded)}
        >
          <Typography>{currentLanguage}</Typography>
          <ArrowDropDown
            className={classNames(classes.arrow, {
              [classes.rotate]: isExpanded
            })}
          />
        </Card>
        <Popper
          className={classes.popover}
          open={isExpanded}
          anchorEl={anchor.current}
          transition
          disablePortal
          placement="bottom-end"
        >
          {({ TransitionProps, placement }) => (
            <Grow
              {...TransitionProps}
              style={{
                transformOrigin:
                  placement === "bottom" ? "right top" : "right bottom"
              }}
            >
              <Paper className={classes.menuPaper}>
                <ClickAwayListener
                  onClickAway={() => setExpandedState(false)}
                  mouseEvent="onClick"
                >
                  {languages.map(lang => (
                    <Menu>
                      <MenuItem
                        className={classes.menuItem}
                        onClick={() => {
                          setExpandedState(false);
                          onLanguageChange(lang.code);
                        }}
                      >
                        {i18n.t("{{ languageName }} - {{ languageCode }}", {
                          context: "button",
                          languageCode: lang.code,
                          languageName: lang.language
                        })}
                      </MenuItem>
                    </Menu>
                  ))}
                </ClickAwayListener>
              </Paper>
            </Grow>
          )}
        </Popper>
      </div>
    );
  }
);
LanguageSwitch.displayName = "LanguageSwitch";
export default LanguageSwitch;
