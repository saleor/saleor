import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    children: theme.mixins.gutters({}),
    constantHeight: {
      height: 56
    },
    hr: {
      border: "none",
      borderTop: `1px solid ${theme.overrides.MuiCard.root.borderColor}`,
      height: 0,
      marginBottom: 0,
      marginTop: 0,
      width: "100%"
    },
    root: theme.mixins.gutters({
      alignItems: "center",
      display: "flex",
      minHeight: 56
    }),
    title: {
      flex: 1,
      lineHeight: 1
    },
    toolbar: {
      marginRight: -theme.spacing.unit * 2
    }
  });

interface CardTitleProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  className?: string;
  height?: "default" | "const";
  title: string | React.ReactNode;
  toolbar?: React.ReactNode;
  onClick?: (event: React.MouseEvent<any>) => void;
}

const CardTitle = withStyles(styles, { name: "CardTitle" })(
  ({
    classes,
    className,
    children,
    height,
    title,
    toolbar,
    onClick,
    ...props
  }: CardTitleProps) => (
    <>
      <div
        className={classNames(classes.root, {
          [className]: !!className,
          [classes.constantHeight]: height === "const"
        })}
        {...props}
      >
        <Typography
          className={classes.title}
          variant="headline"
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
