import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ExtendedPageHeader from "../ExtendedPageHeader";
import Skeleton from "../Skeleton";

const styles = (theme: Theme) =>
  createStyles({
    title: {
      flex: 1,
      paddingBottom: theme.spacing.unit * 2
    }
  });

interface PageHeaderProps extends WithStyles<typeof styles> {
  children?: React.ReactNode;
  className?: string;
  title?: string;
  onBack?();
}

const PageHeader = withStyles(styles)(
  ({ children, classes, className, onBack, title }: PageHeaderProps) => (
    <ExtendedPageHeader
      className={className}
      onBack={onBack}
      title={
        <Typography className={classes.title} variant="title">
          {title !== undefined ? title : <Skeleton style={{ width: "10em" }} />}
        </Typography>
      }
    >
      {children}
    </ExtendedPageHeader>
  )
);
PageHeader.displayName = "PageHeader";
export default PageHeader;
