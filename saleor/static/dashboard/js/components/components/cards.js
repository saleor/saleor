import React from 'react';
import { withStyles } from 'material-ui/styles';

const styles = {
  cardTitle: {
    fontWeight: 300,
    fontSize: '24px'
  },
  cardSubtitle: {
    fontSize: '1.3rem',
    lineHeight: '110%',
    margin: '0.65rem 0 0.52rem 0'
  }
};
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
