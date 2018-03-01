import React from 'react';
import Button from 'material-ui/Button';
import Card, { CardActions, CardContent } from 'material-ui/Card';
import PropTypes from 'prop-types';
import Typography from 'material-ui/Typography';

import { pgettext } from '../../i18n';

const DescriptionCard = (props) => {
  const {
    description,
    descriptionTextLabel,
    editButtonLabel,
    handleEditButtonClick,
    handleRemoveButtonClick,
    removeButtonLabel,
    title,
  } = props;
  return (
    <div>
      <Card>
        <CardContent>
          <Typography variant="display1">
            {title}
          </Typography>
          <Typography variant="title">
            {descriptionTextLabel}
          </Typography>
          <Typography>
            {description}
          </Typography>
          <CardActions>
            <Button
              color="secondary"
              onClick={handleEditButtonClick}
            >
              {editButtonLabel}
            </Button>
            <Button
              color="secondary"
              onClick={handleRemoveButtonClick}
            >
              {removeButtonLabel}
            </Button>
          </CardActions>
        </CardContent>
      </Card>
    </div>
  );
};
DescriptionCard.propTypes = {
  description: PropTypes.string,
  descriptionTextLabel: PropTypes.string,
  editButtonLabel: PropTypes.string,
  handleEditButtonClick: PropTypes.func,
  handleRemoveButtonClick: PropTypes.func,
  removeButtonLabel: PropTypes.string,
  title: PropTypes.string,
};
DescriptionCard.defaultProps = {
  descriptionTextLabel: pgettext('Description card widget description text label', 'Description'),
  removeButtonLabel: pgettext('Category list action link', 'Remove'),
  editButtonLabel: pgettext('Category edit action', 'Edit'),
};

export default DescriptionCard;
