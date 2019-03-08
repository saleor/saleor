import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

export interface TabContainerProps {
  children: React.ReactNode | React.ReactNodeArray;
}

const styles = createStyles({
  root: {
    borderBottom: "1px solid #eeeeee"
  }
});

const TabContainer = withStyles(styles, {
  name: "TabContainer"
})(({ classes, children }: TabContainerProps & WithStyles<typeof styles>) => (
  <div className={classes.root}>{children}</div>
));
TabContainer.displayName = "TabContainer";

export default TabContainer;
