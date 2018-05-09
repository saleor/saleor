import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import PersonIcon from "@material-ui/icons/Person";
import * as CRC from "crc-32";
import Avatar from "material-ui/Avatar";
import Card, { CardContent } from "material-ui/Card";
import * as colors from "material-ui/colors";
import grey from "material-ui/colors/grey";
import ExpansionPanel, {
  ExpansionPanelDetails,
  ExpansionPanelSummary
} from "material-ui/ExpansionPanel";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";

import DateFormatter from "../DateFormatter";

interface TimelineProps {}
interface TimelineNodeProps {
  date: string;
  title: string;
}
interface TimelineNoteProps {
  date: string;
  user: string;
  content: string;
}

const decorate = withStyles(theme => ({
  root: {
    marginLeft: theme.spacing.unit * 8,
    paddingLeft: theme.spacing.unit * 3,
    borderStyle: "solid",
    borderWidth: "0 0 0 2px",
    borderColor: grey[300]
  },
  nodeDot: {
    position: "relative" as "relative",
    left: -theme.spacing.unit * 4 - 1,
    width: theme.spacing.unit * 2,
    height: theme.spacing.unit * 2,
    backgroundColor: theme.palette.secondary.main,
    borderRadius: "100%",
    borderStyle: "solid",
    borderWidth: 2,
    borderColor: grey[300]
  },
  nodeRoot: {
    maxWidth: theme.breakpoints.values.sm,
    marginBottom: theme.spacing.unit * 3,
    display: "flex",
    width: "100%",
    position: "relative" as "relative",
    alignItems: "center",
    minHeight: theme.spacing.unit * 8,
    "&:last-child:after": {
      content: "''",
      position: "absolute" as "absolute",
      width: "2px",
      height: `calc(50% - ${theme.spacing.unit}px)`,
      background: theme.palette.background.default,
      top: `calc(50% + ${theme.spacing.unit}px)`,
      left: `${-theme.spacing.unit * 3 - 2}px`
    }
  },
  nodeDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 3
  },
  noteRoot: {
    position: "relative" as "relative",
    left: -theme.spacing.unit * 8.5,
    maxWidth: `calc(${theme.breakpoints.values.sm}px + ${theme.spacing.unit *
      8.5}px)`,
    marginBottom: theme.spacing.unit * 3
  },
  noteTitle: {
    display: "flex" as "flex",
    alignItems: "center" as "center"
  },
  noteUser: {
    marginLeft: theme.spacing.unit * 5.5
  },
  noteDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 7
  },
  noteContent: {
    paddingLeft: theme.spacing.unit * 10.5
  },
  panel: {
    background: "none",
    "&:before": {
      display: "none"
    }
  },
  noExpander: {
    marginLeft: theme.spacing.unit * 3
  },
  noExpanderNodeDate: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 7
  }
}));
export const Timeline = decorate<TimelineProps>(({ classes, children }) => (
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
  ({ classes, date, user, content }) => {
    const palette = [
      colors.amber,
      colors.blue,
      colors.blueGrey,
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
    return (
      <Card className={classes.noteRoot}>
        <CardContent className={classes.noteTitle}>
          <Avatar
            style={{ background: palette[CRC.str(user) % palette.length] }}
          >
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
    );
  }
);
export default Timeline;
