import React from 'react';
import Button from 'material-ui/Button';
import { withStyles } from 'material-ui/styles';

const styles = {
  flatButton: {
    root: {
      fontWeight: 400,
      fontSize: '1rem',
    },
    raised: {
      color: '#ffffff'
    }
  }
};
const FlatButton = withStyles(styles.flatButton)((props) => {
  return <Button {...props} />;
});
const RaisedButton = withStyles(styles.flatButton)((props) => {
  props.variant = 'raised';
  return <Button {...props} />;
});

export {
  FlatButton,
  RaisedButton,
};
