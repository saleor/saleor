import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

interface CardTitleProps extends React.StatelessComponent {
  className?: string;
  title: string | React.ReactNode;
  toolbar?: React.ReactNode;
  onClick?: (event: React.MouseEvent<any>) => void;
}

const decorate = withStyles(theme => ({
  children: theme.mixins.gutters({}),
  hr: {
    backgroundColor: "#eaeaea",
    border: "none",
    height: 1,
    marginBottom: 0,
    marginTop: 0
  },
  root: theme.mixins.gutters({
    alignItems: "center" as "center",
    display: "flex",
    height: theme.spacing.unit * 6
  }),
  title: {
    flex: 1,
    fontSize: "1rem",
    fontWeight: 600 as 600,
    lineHeight: 1
  },
  toolbar: {
    marginRight: -theme.spacing.unit * 2
  }
}));
const CardTitle = decorate<CardTitleProps>(
  ({ classes, className, children, title, toolbar, onClick, ...props }) => (
    <>
      <div className={classNames(classes.root, className)} {...props}>
        <Typography
          className={classes.title}
          variant="body1"
          onClick={onClick}
          component="span"
        >
          {title}
        </Typography>
        <div className={classes.toolbar}>{toolbar}</div>
      </div>
      <div className={classes.children}>{children}</div>
      <hr className={classes.hr} />
    </>
  )
);
CardTitle.displayName = "CardTitle";
export default CardTitle;
