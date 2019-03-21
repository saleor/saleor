import Avatar from "@material-ui/core/Avatar";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as CRC from "crc-32";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as avatar1 from "../../../images/avatars/avatar1.svg";
import * as avatar10 from "../../../images/avatars/avatar10.svg";
import * as avatar11 from "../../../images/avatars/avatar11.svg";
import * as avatar12 from "../../../images/avatars/avatar12.svg";
import * as avatar13 from "../../../images/avatars/avatar13.svg";
import * as avatar14 from "../../../images/avatars/avatar14.svg";
import * as avatar15 from "../../../images/avatars/avatar15.svg";
import * as avatar16 from "../../../images/avatars/avatar16.svg";
import * as avatar17 from "../../../images/avatars/avatar17.svg";
import * as avatar18 from "../../../images/avatars/avatar18.svg";
import * as avatar19 from "../../../images/avatars/avatar19.svg";
import * as avatar2 from "../../../images/avatars/avatar2.svg";
import * as avatar20 from "../../../images/avatars/avatar20.svg";
import * as avatar3 from "../../../images/avatars/avatar3.svg";
import * as avatar4 from "../../../images/avatars/avatar4.svg";
import * as avatar5 from "../../../images/avatars/avatar5.svg";
import * as avatar6 from "../../../images/avatars/avatar6.svg";
import * as avatar7 from "../../../images/avatars/avatar7.svg";
import * as avatar8 from "../../../images/avatars/avatar8.svg";
import * as avatar9 from "../../../images/avatars/avatar9.svg";
import { DateTime } from "../Date";

const avatars = [
  <SVG src={avatar1} />,
  <SVG src={avatar2} />,
  <SVG src={avatar3} />,
  <SVG src={avatar4} />,
  <SVG src={avatar5} />,
  <SVG src={avatar6} />,
  <SVG src={avatar7} />,
  <SVG src={avatar8} />,
  <SVG src={avatar9} />,
  <SVG src={avatar10} />,
  <SVG src={avatar11} />,
  <SVG src={avatar12} />,
  <SVG src={avatar13} />,
  <SVG src={avatar14} />,
  <SVG src={avatar15} />,
  <SVG src={avatar16} />,
  <SVG src={avatar17} />,
  <SVG src={avatar18} />,
  <SVG src={avatar19} />,
  <SVG src={avatar20} />
];

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      "& span": {
        height: "100%",
        width: "100%"
      },
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
    date: {
      color: theme.typography.caption.color
    },
    root: {
      position: "relative"
    },
    title: {
      alignItems: "center",
      display: "flex",
      justifyContent: "space-between",
      marginBottom: theme.spacing.unit,
      paddingLeft: theme.spacing.unit * 3
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
      <Avatar className={classes.avatar}>
        {avatars[CRC.str(user.email) % avatars.length]}
      </Avatar>
      <div className={classes.title}>
        <Typography>{user.email}</Typography>
        <Typography className={classes.date}>
          <DateTime date={date} />
        </Typography>
      </div>
      <Card className={classes.card}>
        <CardContent className={classes.cardContent}>
          <Typography
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
