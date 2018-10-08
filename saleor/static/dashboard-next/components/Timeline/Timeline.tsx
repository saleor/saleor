import Avatar from "@material-ui/core/Avatar";
import Button from "@material-ui/core/Button";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import deepPurple from "@material-ui/core/colors/deepPurple";
import grey from "@material-ui/core/colors/grey";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import PersonIcon from "@material-ui/icons/Person";
import * as classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";

interface TimelineAddNoteProps {
  message: string;
  onChange(event: React.ChangeEvent<any>);
  onSubmit(event: React.FormEvent<any>);
}

const decorate = withStyles(theme => ({
  avatar: {
    alignSelf: "flex-start" as "flex-start",
    marginRight: theme.spacing.unit * 5.5
  },
  cardActions: {
    direction: "rtl" as "rtl",
    display: "block" as "block",
    maxHeight: 0,
    overflow: "hidden" as "hidden",
    padding: "0 20px",
    transitionDuration: "200ms"
  },
  cardActionsExpanded: {
    maxHeight: theme.spacing.unit * 6
  },
  noteRoot: {
    left: -theme.spacing.unit * 8.5 - 1,
    marginBottom: theme.spacing.unit * 3,
    position: "relative" as "relative",
    width: `calc(100% + ${theme.spacing.unit * 8.5}px)`
  },
  noteTitle: {
    alignItems: "center" as "center",
    display: "flex" as "flex"
  },
  root: {
    borderColor: grey[300],
    borderStyle: "solid",
    borderWidth: "0 0 0 2px",
    marginLeft: theme.spacing.unit * 5.5,
    paddingLeft: theme.spacing.unit * 3
  }
}));

export const Timeline = decorate(({ classes, children }) => (
  <div className={classes.root}>{children}</div>
));
export const TimelineAddNote = decorate<TimelineAddNoteProps>(
  ({ classes, message, onChange, onSubmit }) => (
    <div className={classes.noteRoot}>
      <CardContent className={classes.noteTitle}>
        <Avatar
          style={{ background: deepPurple[500] }}
          className={classes.avatar}
        >
          <PersonIcon />
        </Avatar>
        <TextField
          placeholder={i18n.t("Leave your note here...")}
          onChange={onChange}
          value={message}
          name="message"
          fullWidth
          multiline
        />
      </CardContent>
      <CardActions
        className={classNames([
          classes.cardActions,
          { [classes.cardActionsExpanded]: message }
        ])}
      >
        <Button onClick={onSubmit}>{i18n.t("Add note")}</Button>
      </CardActions>
    </div>
  )
);
export default Timeline;
