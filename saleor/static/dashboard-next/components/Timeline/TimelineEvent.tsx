import grey from "@material-ui/core/colors/grey";
import ExpansionPanel from "@material-ui/core/ExpansionPanel";
import ExpansionPanelDetails from "@material-ui/core/ExpansionPanelDetails";
import ExpansionPanelSummary from "@material-ui/core/ExpansionPanelSummary";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import * as React from "react";

import DateFormatter from "../DateFormatter";

interface TimelineEventProps {
  date: string;
  title: string;
}

const decorate = withStyles(theme => ({
  date: {
    position: "absolute" as "absolute",
    right: theme.spacing.unit * 3
  },
  dot: {
    backgroundColor: theme.palette.primary.main,
    borderColor: grey[300],
    borderRadius: "100%",
    borderStyle: "solid",
    borderWidth: 2,
    height: 16,
    left: -33,
    position: "absolute" as "absolute",
    top: 2,
    width: 16
  },
  noExpander: {
    alignItems: "center" as "center",
    display: "flex" as "flex",
    justifyContent: "space-between" as "space-between",
    marginBottom: theme.spacing.unit,
    marginLeft: theme.spacing.unit,
    width: "100%"
  },
  panel: {
    "&:before": {
      display: "none"
    },
    background: "none",
    width: "100%"
  },
  root: {
    "&:last-child:after": {
      background: theme.palette.background.default,
      content: "''",
      height: "calc(50% - 4px)",
      left: `${-theme.spacing.unit * 3 - 2}px`,
      position: "absolute" as "absolute",
      top: "calc(50% + 4px)",
      width: "2px"
    },
    alignItems: "center",
    display: "flex",
    marginBottom: theme.spacing.unit * 3,
    position: "relative" as "relative",
    width: "100%"
  }
}));

export const TimelineEvent = decorate<TimelineEventProps>(
  ({ classes, children, date, title }) => (
    <div className={classes.root}>
      <span className={classes.dot} />
      {children ? (
        <ExpansionPanel className={classes.panel} elevation={0}>
          <ExpansionPanelSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>{title}</Typography>
            <div className={classes.date}>
              <DateFormatter date={date} />
            </div>
          </ExpansionPanelSummary>
          <ExpansionPanelDetails>
            <Typography>{children}</Typography>
          </ExpansionPanelDetails>
        </ExpansionPanel>
      ) : (
        <div className={classes.noExpander}>
          <Typography>{title}</Typography>
          <DateFormatter date={date} />
        </div>
      )}
    </div>
  )
);
TimelineEvent.displayName = "TimelineEvent";
export default TimelineEvent;
