import Button from "@material-ui/core/Button";
import ClickAwayListener from "@material-ui/core/ClickAwayListener";
import Grow from "@material-ui/core/Grow";
import IconButton from "@material-ui/core/IconButton";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import DeleteIcon from "@material-ui/icons/Delete";
import { ContentState } from "draft-js";
import * as React from "react";

import i18n from "../../i18n";
import Anchor from "../Anchor";
import Toggle from "../Toggle";

interface ImageEntityProps {
  children: React.ReactNode;
  contentState: ContentState;
  entityKey: string;
  onEdit: (entityKey: string) => void;
  onRemove: (entityKey: string) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    anchor: {
      display: "inline-block"
    },
    container: {
      alignItems: "center",
      display: "flex"
    },
    image: { maxWidth: "100%" },
    inline: {
      display: "inline-block"
    },
    root: {
      alignItems: "center",
      display: "flex",
      minHeight: 72,
      padding: theme.spacing.unit * 1.5
    }
  });

const ImageEntity = withStyles(styles, {
  name: "ImageEntity"
})(
  ({
    classes,
    contentState,
    entityKey,
    onEdit,
    onRemove
  }: ImageEntityProps & WithStyles<typeof styles>) => (
    <Toggle>
      {(isOpened, { disable, toggle }) => (
        <>
          <Anchor>
            {anchor => (
              <div className={classes.anchor} ref={anchor}>
                <Popper
                  open={isOpened}
                  anchorEl={anchor.current}
                  transition
                  disablePortal
                  placement="bottom"
                >
                  {({ TransitionProps, placement }) => (
                    <Grow
                      {...TransitionProps}
                      style={{
                        transformOrigin: placement
                      }}
                    >
                      <Paper className={classes.root}>
                        <ClickAwayListener
                          onClickAway={disable}
                          mouseEvent="onClick"
                        >
                          <div className={classes.container}>
                            <Button
                              onClick={() => {
                                disable();
                                onEdit(entityKey);
                              }}
                              color="primary"
                              variant="flat"
                            >
                              {i18n.t("Replace")}
                            </Button>
                            <IconButton onClick={() => onRemove(entityKey)}>
                              <DeleteIcon color="primary" />
                            </IconButton>
                          </div>
                        </ClickAwayListener>
                      </Paper>
                    </Grow>
                  )}
                </Popper>
              </div>
            )}
          </Anchor>
          <img
            className={classes.image}
            src={contentState.getEntity(entityKey).getData().href}
            onClick={toggle}
          />
        </>
      )}
    </Toggle>
  )
);
export default ImageEntity;
