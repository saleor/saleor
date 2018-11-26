import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ExtendedPageHeader from "../ExtendedPageHeader";
import Skeleton from "../Skeleton";

const decorate = withStyles(
  theme => ({
    title: {
      flex: 1,
      paddingBottom: theme.spacing.unit * 2
    }
  }),
  { name: "PageHeader" }
);

interface PageHeaderProps {
  className?: string;
  title?: string;
  onBack?();
}

const PageHeader = decorate<PageHeaderProps>(
  ({ children, classes, className, onBack, title }) => (
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
