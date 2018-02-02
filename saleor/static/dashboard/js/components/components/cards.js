import React from 'react';
import { CardActions as MuiCardActions } from 'material-ui/Card';
import { withStyles } from 'material-ui/styles';

const styles = {
  cardTitle: {
    root: {
      fontWeight: 300,
      fontSize: '24px',
    }
  },
  cardSubtitle: {
    root: {
      fontSize: '1.3rem',
      lineHeight: '110%',
      margin: '0.65rem 0 0.52rem 0',
    }
  },
  cardActions: {
    root: {
      borderTop: '1px solid rgba(160, 160, 160, 0.2)',
      margin: '24px -16px -24px',
      padding: '0 8px',
    }
  }
};
const CardTitle = (props) => {
  return <div style={styles.cardTitle.root} {...props}>{props.children}</div>;
};
const CardSubtitle = (props) => {
  return <div style={styles.cardSubtitle.root} {...props}>{props.children}</div>;
};
const CardActions = withStyles(styles.cardActions)((props) => {
  return <MuiCardActions {...props}>{props.children}</MuiCardActions>;
});

export {
  CardActions,
  CardTitle,
  CardSubtitle
};
