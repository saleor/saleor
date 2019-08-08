import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import React from "react";

import ExtendedPageHeader from "../ExtendedPageHeader";
import Skeleton from "../Skeleton";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "flex"
    },
    title: {
      flex: 1,
      fontSize: 24,
      paddingBottom: theme.spacing.unit * 2
    }
  });

interface PageHeaderProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  className?: string;
  title?: string;
}

const PageHeader = withStyles(styles)(
  ({ children, classes, className, title }: PageHeaderProps) => (
    <ExtendedPageHeader
      className={className}
      title={
        <Typography className={classes.title} variant="h5">
          {title !== undefined ? title : <Skeleton style={{ width: "10em" }} />}
        </Typography>
      }
    >
      <div className={classes.root}>{children}</div>
    </ExtendedPageHeader>
  )
);
PageHeader.displayName = "PageHeader";
export default PageHeader;
