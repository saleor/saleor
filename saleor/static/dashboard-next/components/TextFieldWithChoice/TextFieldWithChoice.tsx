import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import MenuItem from "@material-ui/core/MenuItem";
import Menu from "@material-ui/core/MenuList";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import { createStyles, WithStyles, withStyles } from "@material-ui/core/styles";
import TextField, { TextFieldProps } from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import DropdownIcon from "@material-ui/icons/ArrowDropDown";
import * as React from "react";
import Anchor from "../Anchor";
import MenuToggle from "../MenuToggle";

export type TextFieldWithChoiceProps<TValue = string> = TextFieldProps & {
  ChoiceProps: {
    name: string;
    label: string | React.ReactNode;
    values: Array<{
      label: string | React.ReactNode;
      value: TValue;
    }>;
  };
};

const styles = createStyles({
  adornment: {
    alignItems: "center",
    cursor: "pointer",
    display: "flex"
  },
  menu: {
    zIndex: 10
  }
});

const TextFieldWithChoice = withStyles(styles, {
  name: "TextFieldWithChoices"
})(
  ({
    ChoiceProps,
    InputProps,
    classes,
    onChange,
    ...props
  }: TextFieldWithChoiceProps & WithStyles<typeof styles>) => (
    <Anchor>
      {anchor => (
        <TextField
          {...props}
          onChange={onChange}
          InputProps={{
            ...InputProps,
            endAdornment: (
              <MenuToggle ariaOwns="user-menu">
                {({
                  open: menuOpen,
                  actions: { open: openMenu, close: closeMenu }
                }) => {
                  const handleSelect = value => {
                    onChange({
                      target: {
                        name: ChoiceProps.name,
                        value
                      }
                    } as any);
                    closeMenu();
                  };

                  return (
                    <>
                      <div
                        className={classes.adornment}
                        ref={anchor}
                        onClick={!menuOpen ? openMenu : undefined}
                      >
                        <Typography component="span" variant="caption">
                          {ChoiceProps.label}
                        </Typography>
                        <DropdownIcon />
                      </div>
                      <Popper
                        open={menuOpen}
                        anchorEl={anchor.current}
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
                                  {ChoiceProps.values.map(choice => (
                                    <MenuItem
                                      onClick={() => handleSelect(choice.value)}
                                    >
                                      {choice.label}
                                    </MenuItem>
                                  ))}
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
      )}
    </Anchor>
  )
);
TextFieldWithChoice.displayName = "TextFieldWithChoice";
export default TextFieldWithChoice;
