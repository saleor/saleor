import Avatar from "@material-ui/core/Avatar";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import * as colors from "@material-ui/core/colors";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import PersonIcon from "@material-ui/icons/Person";
import * as CRC from "crc-32";
import * as React from "react";

import { DateTime } from "../Date";
import Hr from "../Hr";

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

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      left: -45,
      position: "absolute",
      top: 0
    },
    card: {
      marginBottom: theme.spacing.unit * 3,
      marginLeft: theme.spacing.unit * 3,
      position: "relative"
    },
    cardContent: {
      "&:last-child": {
        paddingBottom: 16
      }
    },
    content: {
      marginTop: theme.spacing.unit * 2
    },
    root: {
      position: "relative"
    },
    title: {
      alignItems: "center",
      display: "flex",
      justifyContent: "space-between",
      marginBottom: theme.spacing.unit
    }
  });

interface TimelineNoteProps extends WithStyles<typeof styles> {
  date: string;
  message: string | null;
  user: {
    email: string;
  };
}

export const TimelineNote = withStyles(styles, { name: "TimelineNote" })(
  ({ classes, date, user, message }: TimelineNoteProps) => (
    <div className={classes.root}>
      <Avatar
        className={classes.avatar}
        style={{ background: palette[CRC.str(user.email) % palette.length] }}
      >
        <PersonIcon />
      </Avatar>
      <Card className={classes.card}>
        <CardContent className={classes.cardContent}>
          <div className={classes.title}>
            <Typography>{user.email}</Typography>
            <Typography>
              <DateTime date={date} />
            </Typography>
          </div>
          <Hr />
          <Typography
            className={classes.content}
            dangerouslySetInnerHTML={{
              __html: message.replace("\n", "<br />")
            }}
          />
        </CardContent>
      </Card>
    </div>
  )
);
TimelineNote.displayName = "TimelineNote";
export default TimelineNote;
