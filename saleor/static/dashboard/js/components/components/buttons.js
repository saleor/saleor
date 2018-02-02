import React from 'react';
import Button from 'material-ui/Button';
import { withStyles } from 'material-ui/styles';

const styles = {
  flatButton: (theme) => ({
    root: {
      fontWeight: 400,
      fontSize: '1rem',
    },
  }),
};
const FlatButton = withStyles(styles.flatButton)((props) => {
  return <Button {...props} />;
});

export {
  FlatButton
};
