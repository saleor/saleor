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
import Typography from "@material-ui/core/Typography";
import DeleteIcon from "@material-ui/icons/Delete";
import { ContentState } from "draft-js";
import * as React from "react";

import i18n from "../../i18n";
import Link from "../Link";

interface LinkEntityProps {
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
    inline: {
      display: "inline-block"
    },
    popover: {
      zIndex: 1
    },
    root: {
      alignItems: "center",
      display: "flex",
      minHeight: 72,
      padding: `${theme.spacing.unit * 1.5}px ${theme.spacing.unit *
        1.5}px ${theme.spacing.unit * 1.5}px ${theme.spacing.unit * 3}px`
    },
    separator: {
      backgroundColor: theme.palette.grey[300],
      display: "inline-block",
      height: 30,
      marginLeft: theme.spacing.unit * 2,
      marginRight: theme.spacing.unit,
      width: 1
    }
  });

const LinkEntity = withStyles(styles, {
  name: "LinkEntity"
})(
  ({
    classes,
    children,
    contentState,
    entityKey,
    onEdit,
    onRemove
  }: LinkEntityProps & WithStyles<typeof styles>) => {
    const [isOpened, setOpenStatus] = React.useState(false);
    const anchor = React.useRef<HTMLDivElement>();

    const disable = () => setOpenStatus(false);
    const toggle = () => setOpenStatus(!isOpened);

    return (
      <>
        <div className={classes.anchor} ref={anchor}>
          <Popper
            className={classes.popover}
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
                  <ClickAwayListener onClickAway={disable} mouseEvent="onClick">
                    <div className={classes.container}>
                      <Typography className={classes.inline} variant="body2">
                        {contentState.getEntity(entityKey).getData().url}
                      </Typography>
                      <span className={classes.separator} />
                      <Button
                        onClick={() => {
                          disable();
                          onEdit(entityKey);
                        }}
                        color="primary"
                      >
                        {i18n.t("Edit")}
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
        <Link
          href={contentState.getEntity(entityKey).getData().url}
          onClick={toggle}
        >
          {children}
        </Link>
      </>
    );
  }
);
export default LinkEntity;
