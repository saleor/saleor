import React from 'react';
import { withStyles } from 'material-ui/styles';

const styles = (theme) => ({
  cardTitle: {
    fontWeight: 300,
    fontSize: theme.typography.display1.fontSize
  },
  cardSubtitle: {
    fontSize: theme.typography.title.fontSize,
    lineHeight: '110%',
    margin: '0.65rem 0 0.52rem 0'
  }
});
const CardTitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardTitle} {...componentProps}>
        {children}
      </div>
    );
  }
);
const CardSubtitle = withStyles(styles)(
  (props) => {
    const { classes, children, componentProps } = props;
    return (
      <div className={classes.cardSubtitle} {...componentProps}>
        {children}
      </div>
    );
  }
);

export {
  CardTitle,
  CardSubtitle
};
