import Avatar from "@material-ui/core/Avatar";
import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import * as colors from "@material-ui/core/colors";
import grey from "@material-ui/core/colors/grey";
import ExpansionPanel from "@material-ui/core/ExpansionPanel";
import ExpansionPanelDetails from "@material-ui/core/ExpansionPanelDetails";
import ExpansionPanelSummary from "@material-ui/core/ExpansionPanelSummary";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import PersonIcon from "@material-ui/icons/Person";
import * as classNames from "classnames";
import * as CRC from "crc-32";
import * as React from "react";

import i18n from "../../i18n";
import DateFormatter from "../DateFormatter";

interface TimelineNodeProps {
  date: string;
  title: string;
}
interface TimelineNoteProps {
  date: string;
  user: string;
  content: string;
}
interface TimelineAddNoteProps {
  user: string;
  content: string;
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
    transitionDuration: "200ms"
  },
  cardActionsExpanded: {
    maxHeight: theme.spacing.unit * 6
  },
  noExpander: {
    marginLeft: theme.spacing.unit * 3
  },
  noExpanderNodeDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 7
  },
  nodeDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 3
  },
  nodeDot: {
    backgroundColor: theme.palette.secondary.main,
    borderColor: grey[300],
    borderRadius: "100%",
    borderStyle: "solid",
    borderWidth: 2,
    height: theme.spacing.unit * 2,
    left: -theme.spacing.unit * 4 - 1,
    position: "relative" as "relative",
    width: theme.spacing.unit * 2
  },
  nodeRoot: {
    "&:last-child:after": {
      background: theme.palette.background.default,
      content: "''",
      height: `calc(50% - ${theme.spacing.unit}px)`,
      left: `${-theme.spacing.unit * 3 - 2}px`,
      position: "absolute" as "absolute",
      top: `calc(50% + ${theme.spacing.unit}px)`,
      width: "2px"
    },
    alignItems: "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 3,
    minHeight: theme.spacing.unit * 8,
    position: "relative" as "relative",
    width: "100%"
  },
  noteContent: {
    paddingLeft: theme.spacing.unit * 10.5
  },
  noteDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 7
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
  noteUser: {
    marginLeft: theme.spacing.unit * 5.5
  },
  panel: {
    "&:before": {
      display: "none"
    },
    background: "none",
    width: "100%"
  },

  root: {
    borderColor: grey[300],
    borderStyle: "solid",
    borderWidth: "0 0 0 2px",
    marginLeft: theme.spacing.unit * 5.5,
    paddingLeft: theme.spacing.unit * 3
  }
}));
const palette = [
  colors.amber,
  colors.blue,
  colors.cyan,
  colors.deepOrange,
  colors.deepPurple,
  colors.green,
  colors.indigo,
  colors.lightBlue,
  colors.lightGreen,
  colors.lime,
  colors.orange,
  colors.pink,
  colors.purple,
  colors.red,
  colors.teal,
  colors.yellow
].map(color => color[500]);

export const Timeline = decorate(({ classes, children }) => (
  <div className={classes.root}>{children}</div>
));
export const TimelineNode = decorate<TimelineNodeProps>(
  ({ classes, date, children, title }) => (
    <div className={classes.nodeRoot}>
      <span className={classes.nodeDot} />
      {children ? (
        <ExpansionPanel className={classes.panel} elevation={0}>
          <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>{title}</Typography>
            <div className={classes.nodeDate}>
              <DateFormatter date={date} />
            </div>
          </ExpansionPanelSummary>
          <ExpansionPanelDetails>
            <Typography>{children}</Typography>
          </ExpansionPanelDetails>
        </ExpansionPanel>
      ) : (
        <>
          <Typography className={classes.noExpander}>{title}</Typography>
          <div className={classes.noExpanderNodeDate}>
            <DateFormatter date={date} />
          </div>
        </>
      )}
    </div>
  )
);
export const TimelineNote = decorate<TimelineNoteProps>(
  ({ classes, date, user, content }) => (
    <Card className={classes.noteRoot}>
      <CardContent className={classes.noteTitle}>
        <Avatar style={{ background: palette[CRC.str(user) % palette.length] }}>
          <PersonIcon />
        </Avatar>
        <Typography className={classes.noteUser}>{user}</Typography>
        <div className={classes.noteDate}>
          <DateFormatter date={date} />
        </div>
      </CardContent>
      <CardContent>
        <Typography className={classes.noteContent}>{content}</Typography>
      </CardContent>
    </Card>
  )
);
export const TimelineAddNote = decorate<TimelineAddNoteProps>(
  ({ classes, user, content, onChange, onSubmit }) => (
    <div className={classes.noteRoot}>
      <CardContent className={classes.noteTitle}>
        <Avatar
          style={{ background: palette[CRC.str(user) % palette.length] }}
          className={classes.avatar}
        >
          <PersonIcon />
        </Avatar>
        <TextField
          label={i18n.t("Note")}
          placeholder={i18n.t("Leave your note here...")}
          onChange={onChange}
          value={content}
          name="content"
          InputLabelProps={{ shrink: true }}
          fullWidth
          multiline
        />
      </CardContent>
      <CardActions
        className={classNames([
          classes.cardActions,
          { [classes.cardActionsExpanded]: content }
        ])}
      >
        <Button onClick={onSubmit}>{i18n.t("Add note")}</Button>
      </CardActions>
    </div>
  )
);
export default Timeline;
