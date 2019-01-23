import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  WithStyles,
  withStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import DropdownIcon from "@material-ui/icons/ArrowDropDown";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Hr from "../../../components/Hr";
import MenuToggle from "../../../components/MenuToggle";
import i18n from "../../../i18n";
import { SaleType } from "../../../types/globalTypes";
import { FormData } from "../SaleDetailsPage";

export interface SalePricingProps {
  data: FormData;
  defaultCurrency: string;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    adornment: {
      alignItems: "center",
      cursor: "pointer",
      display: "flex"
    },
    menu: {
      zIndex: 10
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "1fr 1fr"
    },
    subheading: {
      gridColumnEnd: "span 2",
      marginBottom: theme.spacing.unit * 2
    }
  });

const SalePricing = withStyles(styles, {
  name: "SalePricing"
})(
  class SalePricingComponent extends React.Component<
    SalePricingProps & WithStyles<typeof styles>
  > {
    anchor = React.createRef<HTMLDivElement>();

    render() {
      const { classes, data, defaultCurrency, disabled, onChange } = this.props;

      return (
        <Card>
          <CardTitle title={i18n.t("Pricing")} />
          <CardContent className={classes.root}>
            <TextField
              disabled={disabled}
              name={"value" as keyof FormData}
              onChange={onChange}
              label={i18n.t("Discount Value")}
              value={data.value}
              type="number"
              fullWidth
              InputProps={{
                endAdornment: (
                  <MenuToggle ariaOwns="user-menu">
                    {({
                      open: menuOpen,
                      actions: { open: openMenu, close: closeMenu }
                    }) => {
                      const handleSelect = (value: SaleType) => {
                        onChange({
                          target: {
                            name: "type",
                            value
                          }
                        } as any);
                        closeMenu();
                      };

                      return (
                        <>
                          <div
                            className={classes.adornment}
                            ref={this.anchor}
                            onClick={!menuOpen ? openMenu : undefined}
                          >
                            <Typography component="span" variant="caption">
                              {data.type === SaleType.FIXED
                                ? defaultCurrency
                                : "%"}
                            </Typography>
                            <DropdownIcon />
                          </div>
                          <Popper
                            open={menuOpen}
                            anchorEl={this.anchor.current}
                            transition
                            disablePortal
                            placement="bottom-end"
                            className={classes.menu}
                          >
                            {({ TransitionProps, placement }) => (
                              <Grow
                                {...TransitionProps}
                                style={{
                                  transformOrigin:
                                    placement === "bottom"
                                      ? "right top"
                                      : "right bottom"
                                }}
                              >
                                <Paper>
                                  <ClickAwayListener
                                    onClickAway={closeMenu}
                                    mouseEvent="onClick"
                                  >
                                    <Menu>
                                      <MenuItem
                                        onClick={() =>
                                          handleSelect(SaleType.FIXED)
                                        }
                                      >
                                        {defaultCurrency}
                                      </MenuItem>
                                      <MenuItem
                                        onClick={() =>
                                          handleSelect(SaleType.PERCENTAGE)
                                        }
                                      >
                                        %
                                      </MenuItem>
                                    </Menu>
                                  </ClickAwayListener>
                                </Paper>
                              </Grow>
                            )}
                          </Popper>
                        </>
                      );
                    }}
                  </MenuToggle>
                )
              }}
            />
          </CardContent>
          <Hr />
          <CardContent className={classes.root}>
            <Typography className={classes.subheading} variant="subheading">
              {i18n.t("Time Frame")}
            </Typography>
            <TextField
              disabled={disabled}
              name={"startDate" as keyof FormData}
              onChange={onChange}
              label={i18n.t("Start Date")}
              value={data.startDate}
              type="date"
              fullWidth
            />
            <TextField
              disabled={disabled}
              name={"endDate" as keyof FormData}
              onChange={onChange}
              label={i18n.t("End Date")}
              value={data.endDate}
              type="date"
              fullWidth
            />
          </CardContent>
        </Card>
      );
    }
  }
);
SalePricing.displayName = "SalePricing";
export default SalePricing;
